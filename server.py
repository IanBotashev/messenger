#!/usr/bin/env python3
import os
import sys
from twisted.internet import protocol, reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from session import *
from packet import *
from twisted.python import log
import traceback
from errors import SessionError
import toml
from constants import CONFIG_FILE, DOCKER_ENV_KEY


class MessagingProtocol(protocol.Protocol):
    def __init__(self, session: ServerSession):
        self.session = session
        self.logged_in = False

    def connectionMade(self):
        log.msg(f"Client connected: {self.transport.getPeer()}")

    def dataReceived(self, data: bytes):
        log.msg("Data received")
        try:
            self.handle_message(data)
        except SessionError as e:
            log.err(f"Session Error: {str(e)}")
            self.transport.write(error_message(str(e)).encode())
        except zlib.error as e:
            log.err("Client seems to be broken. Notifying and breaking connection.")
            message = "\nYour client seems to broken or malformed.\n"
            self.transport.write(error_message(message).encode())
            self.transport.write(message.encode())  # Sending as plaintext so it pops up in their console.
            self.transport.loseConnection()
        except Exception as e:
            log.err(e, "".join(traceback.format_exception(e)))
            self.transport.write(error_message("Internal Server Error").encode())

    def connectionLost(self, reason):
        log.msg(f"Connection lost. {reason!r}")
        if self.logged_in:
            user = self.session.logout_user(self)
            self.send_server_message(self.session.abrupt_leave_announcement.format(user=user))

    def handle_message(self, data):
        """
        Handles a message sent from a client.
        :param data:
        :return:
        """
        message = JsonPacket.decode(data)
        log.msg(f"Handling message: {message}")
        match message.type:
            case PacketType.LOGIN_REQUEST:
                if self.logged_in:
                    raise SessionError("Already logged in!")

                self.session.login_user(message.user, message.password, self)
                log.msg("Syncing login message logs...")
                log.msg(self.session.logged_in_users)
                self.logged_in = True
                self.send_server_message(self.session.join_announcement.format(user=message.user))

            case PacketType.LOGOUT_REQUEST:
                if not self.logged_in:
                    raise SessionError("You need to login first.")

                user = self.session.logout_user(self)
                self.logged_in = False
                self.send_server_message(self.session.leave_announcement.format(user=user))

            case PacketType.LOG_MESSAGE:
                if not self.logged_in:
                    raise SessionError("You need to be logged in to send messages.")

                self.session.log_message(message, self)
                self.update_all_client_logs(self.session.get_latest_message())

            case PacketType.MESSAGE_LOG_SET_REQUEST:
                if not self.logged_in:
                    raise SessionError("You need to be logged in to see messages.")

                self.transport.write(message_log_set(self.session.get_message_log()).encode())

            case PacketType.CREATE_USER:
                self.session.create_new_user(message.username, message.password)

            case PacketType.SERVER_INFO_REQUEST:
                self.transport.write(
                    server_info(
                        self.session.server_name,
                        self.session.msg_char_limit,
                        self.session.name_char_limit,
                        self.session.allow_user_creation,
                        self.session.max_shown_messages
                    ).encode()
                )

            case _:
                log.err("Improper Request")
                self.transport.write(error_message("Improper request.").encode())
                return

        self.transport.write(success_message().encode())

    def send_server_message(self, message):
        """
        Automatically sends a server message.
        :param message:
        :return:
        """
        self.session.log_message_from_server(message)
        self.update_all_client_logs(self.session.get_latest_message())

    def update_all_client_logs(self, message):
        """
        Updates all the currently connected clients logs with a new message.
        :param message:
        :return:
        """
        log.msg("Adding new message to all clients.")
        encoded_message = message_log_addition(message).encode()
        for user in self.session.logged_in_users:
            if user is not None:
                user.transport.write(encoded_message)


class MessagingFactory(protocol.ServerFactory):
    protocol = MessagingProtocol

    def __init__(self):
        self.session = ServerSession()

    def buildProtocol(self, addr):
        return MessagingProtocol(self.session)


def folder_check(config):
    """
    If we're not in a container, make our data folder exists. If not, create it.
    Can't log, since our log file is in the data folder. Instead we print everything normally to the console.
    :param config:
    :return:
    """
    in_docker = os.getenv(DOCKER_ENV_KEY)
    data_folder = config['structure']['data_folder']
    if not in_docker and not os.path.exists(f"{data_folder}"):
        print("Not in docker container, and persistent folder does not exist. Creating...")
        os.mkdir(f'{data_folder}')


def get_log_file(config):
    """
    Gets the location of the log file for this server.
    :param config:
    :return:
    """
    return os.path.join(config['structure']['data_folder'], config['structure']['log_file'])


if __name__ == "__main__":
    config = toml.load(CONFIG_FILE)
    folder_check(config)
    log.startLogging(open(get_log_file(config), 'w'))

    endpoint = TCP4ServerEndpoint(reactor, toml.load(CONFIG_FILE)['port'])
    endpoint.listen(MessagingFactory())
    reactor.run()
