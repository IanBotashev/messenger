from tkinter import *
from tkinter import messagebox
from twisted.internet import reactor
from twisted.python import log
from message import *


class GUI(object):
    def __init__(self, root, client):
        self.message_log = []
        self.root = root
        self.client = client

        self.username = StringVar()
        self.password = StringVar()
        self.message = StringVar()

        self.root.bind('<Return>', self.log_message)
        self.root.title("Messaging")
        self.frame = Frame(root)
        self.textbox = Text(self.frame)
        quit_button = Button(self.frame, text='Quit', command=self.on_quit)
        reset_button = Button(self.frame, text='Reset', command=self.resend_message_log)
        login_button = Button(self.frame, text='Login', command=self.login_popup)
        logout_button = Button(self.frame, text='Logout', command=self.logout)
        create_user_button = Button(self.frame, text='Create User', command=self.create_user_popup)
        self.message_input = Entry(self.frame, textvariable=self.message)
        log_message_input_button = Button(self.frame, text='Submit', command=self.log_message)
        self.login_dialog = None

        self.frame.pack()
        login_button.grid(row=0, column=5)
        logout_button.grid(row=1, column=5)
        reset_button.grid(row=2, column=5)
        self.textbox.grid(row=0, column=0, columnspan=5, rowspan=5)
        self.textbox.configure(state="disabled")
        self.message_input.grid(row=5, column=1)
        log_message_input_button.grid(row=6, column=1)
        quit_button.grid(row=3, column=5)
        create_user_button.grid(row=4, column=5)

        self.textbox.tag_configure("server_message", foreground="red")

    def resend_message_log(self):
        """
        Requests the server to reset our message log.
        :return:
        """
        self.client.transport.write(message_log_set_request().encode())

    def add_message(self, message):
        """
        Adds a message into the textbox.
        :param message:
        :return:
        """
        self.message_log.append(message)
        self.update_text_box_content()

    def set_message_log(self, new_log):
        """
        Sets the current message log to a new one.
        :param new_log:
        :return:
        """
        self.message_log = new_log
        self.update_text_box_content()

    def update_text_box_content(self):
        """
        Updates the textbox with up-to-date information of the message log.
        :return:
        """
        self.message_log.sort()
        self.textbox.configure(state="normal")
        self.textbox.delete('1.0', END)
        for message in self.message_log:
            if message.sender.name == "server":
                self.textbox.insert('1.0', f"{message.message}\n", "server_message")
            else:
                self.textbox.insert('1.0', f"{message.sender.name}: {message.message}\n")
        self.textbox.configure(state="disabled")

    def log_message(self, event=None):
        """
        Logs a message with the server
        :return:
        """
        self.client.transport.write(log_message(self.message.get()).encode())
        self.message_input.delete(0, END)

    def logout(self):
        """
        Log outs the user.
        :return:
        """
        self.client.transport.write(logout_message().encode())

    def login(self):
        """
        Logs in user.
        :return:
        """
        self.client.transport.write(login_message(self.username.get(), self.password.get()).encode())
        self.login_dialog.destroy()

    def request_new_user(self):
        """
        Creates new user
        :return:
        """
        self.client.transport.write(create_user(self.username.get(), self.password.get()).encode())
        self.login_dialog.destroy()

    def login_popup(self):
        """
        Pops up a window asking the user to login.
        :return:
        """
        self.login_dialog = Toplevel(self.root)
        self.login_dialog.title("Create new user.")

        username = Label(self.login_dialog, text="Username:")
        name_entry = Entry(self.login_dialog, textvariable=self.username)
        password = Label(self.login_dialog, text="Password:")
        password_entry = Entry(self.login_dialog, textvariable=self.password, show="*")
        submit_button = Button(self.login_dialog, text='Submit', command=self.login)

        username.grid(row=0, column=0)
        name_entry.grid(row=0, column=1)
        password.grid(row=1, column=0)
        password_entry.grid(row=1, column=1)
        submit_button.grid(row=2, column=1)

    def create_user_popup(self):
        """
        Pops up a window to create a new user.
        :return:
        """
        self.login_dialog = Toplevel(self.root)
        self.login_dialog.title("Create a new user.")

        username = Label(self.login_dialog, text="New Username:")
        name_entry = Entry(self.login_dialog, textvariable=self.username)
        password = Label(self.login_dialog, text="New Password:")
        password_entry = Entry(self.login_dialog, textvariable=self.password, show="*")
        submit_button = Button(self.login_dialog, text='Submit', command=self.request_new_user)

        username.grid(row=0, column=0)
        name_entry.grid(row=0, column=1)
        password.grid(row=1, column=0)
        password_entry.grid(row=1, column=1)
        submit_button.grid(row=2, column=1)

    def on_quit(self):
        log.msg("Quitting...")
        reactor.stop()
