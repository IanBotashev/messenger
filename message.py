import time
from enum import Enum
import pickle


STANDARD_PORT = 49153


class MessageType(Enum):
    LOGIN_REQUEST = "LOGIN_REQUEST"
    LOGOUT_REQUEST = "LOGOUT_REQUEST"
    LOG_MESSAGE = "LOG_MESSAGE"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    MESSAGE_LOG_SET = "MESSAGE_LOG_SET"  # Sets a clients message log to that of the servers.
    MESSAGE_LOG_SET_REQUEST = "MESSAGE_LOG_SET_REQUEST"  # A way for clients to request to be sent a new message log set.
    MESSAGE_LOG_ADDITION = "MESSAGE_LOG_ADDITION"  # Adds a new entry into the logs of each client.
    CREATE_USER = "CREATE_USER"  # Adds a new entry into the logs of each client.


class JsonMessage:
    """
    A class to represent a certain kind of message, be it success or failure for example.
    """
    def __init__(self, m_type: MessageType = None, **kwargs):
        self.type = m_type
        self.__dict__.update(kwargs)

    def encode(self):
        """
        Converts this message into a json byte string.
        :return:
        """
        return pickle.dumps(self)

    @staticmethod
    def decode(byte_string):
        """
        Decodes a byte string into a type of this class, returning an instance.
        :return:
        """
        return pickle.loads(byte_string)

    def __str__(self):
        return str(vars(self))


def login_message(user, password):
    """
    Creates a JsonMessage instance with needed information for a login request.
    :param user:
    :param password:
    :return:
    """
    return JsonMessage(MessageType.LOGIN_REQUEST, user=user, password=password)


def log_message(message):
    """
    Creates a JsonMessage instance with needed information to log a message with the server.
    :param message:
    :return:
    """
    return JsonMessage(MessageType.LOG_MESSAGE, content=message, timestamp=time.time())


def error_message(content):
    """
    Creates a JsonMessage instance that signifies an error occurred to the other party.
    :param content:
    :return:
    """
    return JsonMessage(MessageType.ERROR, content=content)


def success_message():
    """
    Creates a JsonMessage instance that signifies an action was successful.
    :param content:
    :return:
    """
    return JsonMessage(MessageType.SUCCESS)


def message_log_addition(content):
    """
    Creates a JsonMessage instance that updates all clients about a new message log.
    :param content:
    :return:
    """
    return JsonMessage(MessageType.MESSAGE_LOG_ADDITION, content=content)


def message_log_set(log):
    """
    Creates a JsonMessage instance that updates all clients about a new message log.
    :param log:
    :return:
    """
    return JsonMessage(MessageType.MESSAGE_LOG_SET, content=log)


def logout_message():
    """
    Creates a JsonMessage instance that can log out a user.
    :return:
    """
    return JsonMessage(MessageType.LOGOUT_REQUEST)


def message_log_set_request():
    """
    Requests that the current client be updated on the message log entirely.
    :return:
    """
    return JsonMessage(MessageType.MESSAGE_LOG_SET_REQUEST)


def create_user(username, password):
    """
    Requests to create a new user.
    :param username:
    :param password:
    :return:
    """
    return JsonMessage(MessageType.CREATE_USER, username=username, password=password)

