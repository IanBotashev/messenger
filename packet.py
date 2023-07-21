import copy
import time
from enum import Enum
import json
import zlib
import base64
from session import Message


class PacketType(Enum):
    LOGIN_REQUEST = "LOGIN_REQUEST"
    LOGOUT_REQUEST = "LOGOUT_REQUEST"
    LOG_MESSAGE = "LOG_MESSAGE"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    MESSAGE_LOG_SET = "MESSAGE_LOG_SET"  # Sets a clients message log to that of the servers.
    MESSAGE_LOG_SET_REQUEST = "MESSAGE_LOG_SET_REQUEST"  # A way for clients to request to be sent a new message log set
    MESSAGE_LOG_ADDITION = "MESSAGE_LOG_ADDITION"  # Adds a new entry into the logs of each client.
    CREATE_USER = "CREATE_USER"  # Adds a new entry into the logs of each client.


class JsonPacket:
    """
    A class to represent a certain kind of message, be it success or failure for example.
    """
    def __init__(self, m_type: PacketType = None, **kwargs):
        self.type = m_type
        self.__dict__.update(kwargs)

    def encode(self):
        """
        Converts this message into a json byte string.
        :return:
        """
        data = copy.deepcopy(vars(self))
        data['type'] = data['type'].name
        return base64.b64encode(zlib.compress(json.dumps(data).encode()))

    @staticmethod
    def decode(byte_string):
        """
        Decodes a byte string into a type of this class, returning an instance.
        :return:
        """
        packet = JsonPacket()
        raw_packet = json.loads(zlib.decompress(base64.b64decode(byte_string)))
        raw_packet['type'] = PacketType[raw_packet['type']]
        packet.__dict__ = raw_packet
        return packet

    @staticmethod
    def encode_message_log(log):
        """
        Compiles a list of messages into one string.
        :param log:
        :return:
        """
        result = []
        for message in log:
            result.append(str(message))

        return json.dumps(result)

    @staticmethod
    def decode_message_log(string):
        """
        Converts a compiled version of a message log back to it's normal form of objects.
        :param string:
        :return:
        """
        decompiled_list = json.loads(string)
        result = []
        for string in decompiled_list:
            result.append(Message.from_string(string))

        return result

    def __str__(self):
        return str(vars(self))


def login_message(user, password):
    """
    Creates a JsonPacket instance with needed information for a login request.
    :param user:
    :param password:
    :return:
    """
    return JsonPacket(PacketType.LOGIN_REQUEST, user=user, password=password)


def log_message(message):
    """
    Creates a JsonPacket instance with needed information to log a message with the server.
    :param message:
    :return:
    """
    return JsonPacket(PacketType.LOG_MESSAGE, content=message, timestamp=time.time())


def error_message(content):
    """
    Creates a JsonPacket instance that signifies an error occurred to the other party.
    :param content:
    :return:
    """
    return JsonPacket(PacketType.ERROR, content=content)


def success_message():
    """
    Creates a JsonPacket instance that signifies an action was successful.
    :param content:
    :return:
    """
    return JsonPacket(PacketType.SUCCESS)


def message_log_addition(content):
    """
    Creates a JsonPacket instance that updates all clients about a new message log.
    :param content:
    :return:
    """
    return JsonPacket(PacketType.MESSAGE_LOG_ADDITION, content=str(content))


def message_log_set(log):
    """
    Creates a JsonPacket instance that updates all clients about a new message log.
    :param log:
    :return:
    """
    return JsonPacket(PacketType.MESSAGE_LOG_SET, content=JsonPacket.encode_message_log(log))


def logout_message():
    """
    Creates a JsonPacket instance that can log out a user.
    :return:
    """
    return JsonPacket(PacketType.LOGOUT_REQUEST)


def message_log_set_request():
    """
    Requests that the current client be updated on the message log entirely.
    :return:
    """
    return JsonPacket(PacketType.MESSAGE_LOG_SET_REQUEST)


def create_user(username, password):
    """
    Requests to create a new user.
    :param username:
    :param password:
    :return:
    """
    return JsonPacket(PacketType.CREATE_USER, username=username, password=password)

