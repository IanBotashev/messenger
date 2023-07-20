import sys
from message import JsonMessage, MessageType, STANDARD_PORT
from twisted.internet import reactor, tksupport
from twisted.python import log
from twisted.internet.protocol import Protocol, ClientFactory
from tkinter import *
from tkinter import messagebox
from gui import GUI


class Client(Protocol):
    def __init__(self):
        self.gui = None

    def connectionMade(self):
        root = Tk()
        tksupport.install(root)
        self.gui = GUI(root, self)

    def dataReceived(self, data):
        message = JsonMessage.decode(data)
        if message.type == MessageType.MESSAGE_LOG_ADDITION:
            self.gui.add_message(message.content)
        elif message.type == MessageType.MESSAGE_LOG_SET:
            self.gui.set_message_log(message.content)
        elif message.type == MessageType.ERROR:
            messagebox.showerror("Session Error", message.content)
        elif message.type == MessageType.SUCCESS:
            messagebox.showinfo("Success!", "Success!")


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
