import customtkinter
from tkinter import *
from twisted.internet import reactor
from packet import *


class CredentialsPopup(customtkinter.CTkToplevel):
    def __init__(self, master, title="Credentials", username_prompt="Username", password_prompt="Password", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master = master
        self.username_prompt = username_prompt
        self.password_prompt = password_prompt
        self.credentials = None
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.title(title)
        self.lift()
        self.after(10, self.create_widgets)
        self.grab_set()

    def create_widgets(self):
        """
        Creates the username and password widgets.
        :return:
        """
        username_label = customtkinter.CTkLabel(
            master=self,
            width=150,
            wraplength=150,
            fg_color="transparent",
            text=self.username_prompt,
            font=("Arial", 25)
        )
        username_label.grid(row=0, column=0, padx=(15, 0), pady=15)
        self.username_entry = customtkinter.CTkEntry(
            master=self,
            width=230,
            font=("Arial", 25)
        )
        self.username_entry.grid(row=0, column=1, pady=15)

        password_label = customtkinter.CTkLabel(
            master=self,
            width=300,
            wraplength=300,
            fg_color="transparent",
            text=self.password_prompt,
            font=("Arial", 25)
        )
        password_label.grid(row=1, column=0, padx=(15, 0), pady=(0, 15))
        self.password_entry = customtkinter.CTkEntry(
            master=self,
            width=230,
            show="*",
            font=("Arial", 25)
        )
        self.password_entry.grid(row=1, column=1, pady=(0, 15), padx=15)

        close_button = customtkinter.CTkButton(self, text="Cancel", command=self.on_closing)
        close_button.grid(row=2, column=0, padx=15, pady=15)

        submit_button = customtkinter.CTkButton(self, text="Submit", command=self.on_submit)
        submit_button.grid(row=2, column=1, padx=15, pady=15)

    def on_submit(self):
        self.credentials = (self.username_entry.get(), self.password_entry.get())
        self.grab_release()
        self.destroy()

    def on_closing(self):
        self.grab_release()
        self.destroy()

    def get_credentials(self):
        """
        Asks for credentiasl from the user.
        :return:
        """
        self.master.wait_window(self)
        return self.credentials


class ScrollableMessageBox(customtkinter.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.message_log = []
        self.labels_list = []

    def add_message(self, message):
        """
        Draw a new message onto the screen.
        :param message:
        :return:
        """
        self.message_log.append(message)
        self.draw_new_message(message)

    def clear(self):
        """
        Destroys all the labels in this message box.
        Does not clear it's message log.
        :return:
        """
        for label in self.labels_list:
            label.destroy()
        self.labels_list = []

    def draw_new_message(self, message):
        """
        Draws a new message and inserts it into the top of the frame.
        :param side_to_insert:
        :param message:
        :return:
        """
        if message.sender.name == "server":
            label = customtkinter.CTkLabel(self, text=f"{message.message}", font=("Arial", 25), text_color="red")
        else:
            label = customtkinter.CTkLabel(
                self,
                text=f"{message.sender.name}: {message.message}",
                font=("Arial", 25)
            )
        # label.grid(row=len(self.labels_list), column=0, padx=(0, 0), stick='w')
        previous_label = None
        if len(self.labels_list) > 0:
            previous_label = self.labels_list[-1]

        label.pack(before=previous_label, anchor="w", side=TOP)
        self.labels_list.append(label)

    def draw_all_messages(self):
        """
        Takes everything in the message log and draws it to the screen.
        First clears everything from the labels list.
        :return:
        """
        self.clear()
        self.message_log.sort()
        for message in self.message_log:  # Go in reverse
            self.draw_new_message(message)

    def set_message_log(self, new_log):
        """
        Completely wipes our message log and sets it to the new one.
        :param new_log:
        :return:
        """
        self.message_log = new_log
        self.draw_all_messages()


class ClientApp(customtkinter.CTk):
    def __init__(self, client):
        super().__init__()
        self.client = client

        self.title("Messenger Client")
        self.grid_rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.message_box_height = 500
        self.message_box_width = 1000

        self.message_box = ScrollableMessageBox(
            master=self,
            width=self.message_box_width
        )

        self.sidebar = customtkinter.CTkFrame(self)
        self.configure_sidebar(self.sidebar)

        self.entry_box = customtkinter.CTkFrame(self)
        self.configure_entry_box(self.entry_box)

        self.message_box.grid(row=0, column=0, padx=15, pady=(15, 0))
        self.message_box.configure(width=self.message_box_width, height=self.message_box_height)
        self.entry_box.grid(row=1, column=0, padx=15, pady=(8, 15), sticky='nw')
        self.entry_box.configure(width=self.message_box_width/4 * 3, height=50)
        self.sidebar.grid(row=0, column=1, sticky="e", padx=(0, 15), pady=15)

    def configure_entry_box(self, entry_box_frame):
        """
        Configures the entry box with an entry widget and a button to submit.
        :param entry_box_frame:
        :return:
        """
        self.entry = customtkinter.CTkEntry(
            entry_box_frame,
        )
        submit_button = customtkinter.CTkButton(
            entry_box_frame,
            font=("Arial", 25),
            text="Send",
            command=self.log_message,
        )
        self.bind("<Return>", self.log_message)

        self.entry.grid(row=0, column=0, padx=(0, 10))
        self.entry.configure(width=self.message_box_width/8 * 7)
        submit_button.grid(row=0, column=1)

    def configure_sidebar(self, sidebar_frame):
        """
        Adds button to the sidebar, such as login.
        :param sidebar_frame:
        :return:
        """
        buttons = [
            ("Login", self.login_popup),
            ("Reload", self.resend_message_log),
            ("Logout", self.logout),
            ("Create User", self.create_user_popup),
            ("Quit", self.on_quit),
        ]
        for i in range(len(buttons)):
            button_info = buttons[i]
            button = customtkinter.CTkButton(
                sidebar_frame,
                font=("Arial", 25),
                text=button_info[0],
                command=button_info[1]
            )

            padding_y = (0, 10)
            if i == len(buttons) - 1:
                padding_y = (0, 0)
            button.grid(row=i, column=0, pady=padding_y)

    def credentials_popup(self, username_prompt, password_prompt):
        """
        Generic pop up to ask for credentials, that being a username or password. Can be used for login
        or user creation.
        :return:
        """

    def on_quit(self):
        """
        When the user presses the "quit" button.
        :return:
        """
        reactor.stop()
        self.quit()

    def resend_message_log(self):
        """
        When the user presses the "reload" button.
        :return:
        """
        self.client.transport.write(message_log_set_request().encode())

    def login_popup(self):
        """
        When the user presses the "login" button.
        :return:
        """
        dialog = CredentialsPopup(self, title="Login")
        credentials = dialog.get_credentials()
        if credentials is not None:
            self.client.transport.write(login_message(credentials[0], credentials[1]).encode())

    def logout(self):
        """
        When the user presses the "logout" button.
        :return:
        """
        self.client.transport.write(logout_message().encode())
        self.message_box.clear()

    def create_user_popup(self):
        """
        When the user presses the "Create user" button.
        :return:
        """
        dialog = CredentialsPopup(
            self,
            title="Create new user",
            username_prompt="New Username",
            password_prompt="New Passsword"
        )
        credentials = dialog.get_credentials()
        if credentials is not None:
            self.client.transport.write(create_user(credentials[0], credentials[1]).encode())

    def log_message(self, event=None):
        """
        When the user presses the "send" button.
        The reason for the empty "event" variable is because the Tkinter method bind to bind a keybind will
        pass in the extra variable, which we don't actually use, so it gets ignored.
        :param event:
        :return:
        """
        self.client.transport.write(log_message(self.entry.get()).encode())
        self.entry.delete(0, END)
