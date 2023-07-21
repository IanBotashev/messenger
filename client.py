import sys

from CTkMessagebox import CTkMessagebox

from message import JsonMessage, MessageType, STANDARD_PORT
from twisted.internet import reactor, tksupport
from twisted.python import log
from twisted.internet.protocol import Protocol, ClientFactory
import customtkinter
from tkinter import messagebox
from client_gui import ClientApp


class Client(Protocol):
    def __init__(self):
        self.gui = None

    def connectionMade(self):
        customtkinter.set_default_color_theme("blue")
        customtkinter.set_appearance_mode("dark")
        self.gui = ClientApp(self)
        tksupport.install(self.gui)

    def dataReceived(self, data):
        message = JsonMessage.decode(data)
        if message.type == MessageType.MESSAGE_LOG_ADDITION:
            self.gui.message_box.add_message(message.content)
        elif message.type == MessageType.MESSAGE_LOG_SET:
            self.gui.message_box.set_message_log(message.content)
        elif message.type == MessageType.ERROR:
            CTkMessagebox(title="Session Error", message=message.content, icon="warning", master=self.gui)
        elif message.type == MessageType.SUCCESS:
            CTkMessagebox(title="Success", message="Success!", icon="check", master=self.gui)


class MessagingClientFactory(ClientFactory):
    def startedConnecting(self, connector):
        log.msg("Trying to connect...")

    def buildProtocol(self, addr):
        log.msg('Connected.')
        return Client()

    def clientConnectionLost(self, connector, reason):
        log.msg('Lost connection.  Reason:', reason)

    def clientConnectionFailed(self, connector, reason):
        log.msg('Connection failed. Reason:', reason)


if __name__ == "__main__":
    log.startLogging(sys.stdout)
    reactor.connectTCP("192.168.1.90", STANDARD_PORT, MessagingClientFactory())
    reactor.run()
    sys.exit()
