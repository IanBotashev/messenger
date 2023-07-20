import time
from errors import SessionError
import sqlite3
from twisted.python import log
import toml
from constants import CONFIG_FILE


class User:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return type(other) == type(self) and self.name == other.name

    def __repr__(self):
        return f"User({self.name})"


class Message:
    def __init__(self, id: int, user: User, message: str, timestamp):
        """
        Represents a message from one user.
        :param id:
        :param user:
        :param message:
        :param timestamp:
        """
        self.id = id
        self.sender = user
        self.message = message
        self.timestamp = timestamp

    def __lt__(self, other):
        if type(other) != type(self):
            return False

        return self.timestamp < other.timestamp

    def __repr__(self):
        return f"Message({self.id}, {self.sender}, {self.message!r})"


class ServerSession:
    def __init__(self):
        self.server_user_name = None
        self.server_user_pass = None
        self.allow_user_creation = None
        self.msg_char_limit = None
        self.name_char_limit = None
        self.max_shown_messages = None
        self.leave_announcement = None
        self.join_announcement = None
        self.abrupt_leave_announcement = None
        self.database = None
        self.get_toml_config()

        self.con = sqlite3.connect(self.database)
        self.generate_database()
        self.logged_in_users = {}  # Relate twister protocol instances to users.
        self.server_user = self.login_user(self.server_user_name, self.server_user_pass, None)
        log.msg("Server successfully logged in.")

    def get_toml_config(self, name=CONFIG_FILE):
        """
        Gets the toml config file and populates needed variables with the values.
        :param name:
        :return:
        """
        config = toml.load(name)
        # Filthy, yes.
        self.server_user_name = config['session']['server_user']['name']
        self.server_user_pass = config['session']['server_user']['password']
        self.database = config['session']['database']['db']
        self.allow_user_creation = config['session']['database']['allow_user_creation']
        self.msg_char_limit = config['session']['database']['message_character_limit']
        self.name_char_limit = config['session']['database']['username_character_limit']
        self.max_shown_messages = config['session']['database']['max_shown_messages']
        self.leave_announcement = config['session']['announcements']['leave']
        self.join_announcement = config['session']['announcements']['join']
        self.abrupt_leave_announcement = config['session']['announcements']['abrupt_leave']

    def generate_database(self):
        """
        Generates the database if it already was not so.
        :return:
        """
        log.msg("Generating database...")
        generate_database_queries = [
            f'CREATE TABLE IF NOT EXISTS users(name text PRIMARY KEY, password text NOT NULL CHECK(typeof("name") = "text" AND length("name") <= {self.name_char_limit}));',
            f'CREATE TABLE IF NOT EXISTS messages(id integer PRIMARY KEY AUTOINCREMENT, message text NOT NULL, timestamp integer NOT NULL, sender text NOT NULL, FOREIGN KEY(sender) REFERENCES users(name) CHECK(typeof("message") = "text" AND length("message") <= {self.msg_char_limit}));',
            f"INSERT OR IGNORE INTO users(name, password) VALUES('{self.server_user_name}', '{self.server_user_pass}');"
        ]
        for query in generate_database_queries:
            cur = self.con.cursor()
            print(query)
            cur.execute(query)
        self.con.commit()

    def log_message(self, message, protocol):
        """
        Adds a raw message to the message log.
        :param message:
        :param protocol:
        :return:
        """
        if len(message.content) > self.msg_char_limit:
            raise SessionError(f"Message is over {self.msg_char_limit} characters, not logging.")

        self.insert_message_into_database(self.logged_in_users[protocol], message.content, message.timestamp)

    def log_message_from_server(self, message):
        """
        Adds a message from the server.
        :param message:
        :return:
        """
        self.insert_message_into_database(self.server_user, message, time.time())

    def insert_message_into_database(self, sender, message, timestamp):
        """
        Inserts the json of a message into the databaase.
        :param message:
        :param sender:
        :param timestamp:
        :return:
        """
        query = "INSERT INTO messages(message, timestamp, sender) VALUES(?, ?, ?)"
        cur = self.con.cursor()
        cur.execute(query, (message, timestamp, sender.name))
        self.con.commit()

    def login_user(self, user, password, protocol):
        """
        Logs in a user.
        Returns the instance of the object that was created.
        :param user:
        :param password:
        :param protocol:
        :return:
        """
        cur = self.con.cursor()
        query = "SELECT name FROM users WHERE name=? AND password=?;"
        user = cur.execute(query, (user, password)).fetchone()
        if not user:
            raise SessionError("Username or Password incorrect. Please try again.")

        login_user = User(user[0])
        if login_user in self.logged_in_users.values():
            raise SessionError(f"Account {user[0]!r} is already logged in.")
        self.logged_in_users[protocol] = login_user

        return login_user

    def logout_user(self, protocol):
        """
        Logs out the user associated with this protocol.
        Returns the name of the user that logged out.
        :param protocol:
        :return:
        """
        user = self.logged_in_users[protocol]
        del self.logged_in_users[protocol]
        return user.name

    def get_message_log(self, length=None):
        """
        Gets the message log up to a certain length, default being the set variable MAX_SHOWN_MESSAGES.
        :param length:
        :return:
        """
        # Set our default parameter.
        if length is None:
            length = self.max_shown_messages

        query = f"SELECT * FROM messages ORDER BY id DESC LIMIT {length};"
        cur = self.con.cursor()
        messages = cur.execute(query).fetchall()
        print(messages)
        result = []
        for message in messages:
            result.append(self.from_database_to_message_instance(message))

        return result

    def get_latest_message(self):
        """
        Returns the latest message in the table.
        :return:
        """
        query = "SELECT * FROM messages ORDER BY id DESC LIMIT 1;"
        cur = self.con.cursor()
        latest_message = cur.execute(query).fetchone()
        return self.from_database_to_message_instance(latest_message)

    def create_new_user(self, username, password):
        """
        Creates a new user in the database.
        :param username:
        :param password:
        :return:
        """
        query = "INSERT INTO users(name, password) VALUES (?, ?);"
        cur = self.con.cursor()
        cur.execute(query, (username, password))
        self.con.commit()

    @staticmethod
    def from_database_to_message_instance(db_tuple):
        """
        Converts a databse tuple output into a message instance.
        :param db_tuple:
        :return:
        """
        return Message(db_tuple[0], User(db_tuple[3]), db_tuple[1], db_tuple[2])
