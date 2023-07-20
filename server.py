import sys

from twisted.internet import protocol, reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from session import *
from message import *
from twisted.python import log
import traceback
from errors import SessionError


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
            log.msg(f"Session Error: {str(e)}")
            self.transport.write(error_message(str(e)).encode())
        except Exception as e:
            log.err(e, "".join(traceback.format_exception(e)))
            self.transport.write(error_message("Internal Server Error").encode())

    def connectionLost(self, reason):
        log.msg(f"Connection lost. {reason!r}")
        if self.logged_in:
            user = self.session.logout_user(self)
            self.send_server_message(ABRUPT_LEAVE_MESSAGE.format(user=user))

    def handle_message(self, data):
        """
        Handles a message sent from a client.
        :param data:
        :return:
        """
        message = JsonMessage.decode(data)
        log.msg(f"Handling message: {message}")
        match message.type:
            case MessageType.LOGIN_REQUEST:
                if self.logged_in:
                    raise SessionError("Already logged in!")

                self.session.login_user(message.user, message.password, self)
                log.msg("Syncing login message logs...")
                log.msg(self.session.logged_in_users)
                self.logged_in = True
                self.send_server_message(JOIN_MESSAGE.format(user=message.user))

            case MessageType.LOGOUT_REQUEST:
                if not self.logged_in:
                    raise SessionError("You need to login first.")

                user = self.session.logout_user(self)
                self.logged_in = False
                self.send_server_message(LEAVE_MESSAGE.format(user=user))

            case MessageType.LOG_MESSAGE:
                if not self.logged_in:
                    raise SessionError("You need to be logged in to send messages.")

                self.session.log_message(message, self)
                self.update_all_client_logs(self.session.get_latest_message())

            case MessageType.MESSAGE_LOG_SET_REQUEST:
                if not self.logged_in:
                    raise SessionError("You need to be logged in to see messages.")

                self.transport.write(message_log_set(self.session.get_message_log()).encode())

            case MessageType.CREATE_USER:
                self.session.create_new_user(message.username, message.password)

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


if __name__ == "__main__":
    log.startLogging(sys.stdout)
    endpoint = TCP4ServerEndpoint(reactor, STANDARD_PORT)
    endpoint.listen(MessagingFactory())
    reactor.run()
