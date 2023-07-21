#!/usr/bin/env python3
import sys
from packet import JsonPacket, PacketType
from constants import STANDARD_PORT
from twisted.internet import reactor, tksupport
from twisted.python import log
from twisted.internet.protocol import Protocol, ClientFactory
import customtkinter
from client_gui import ClientApp, Popup
from session import Message
import traceback
import argparse


class Client(Protocol):
    def __init__(self):
        self.gui = None

    def connectionMade(self):
        customtkinter.set_default_color_theme("blue")
        customtkinter.set_appearance_mode("dark")
        self.gui = ClientApp(self)
        tksupport.install(self.gui)

    def dataReceived(self, data):
        try:
            message = JsonPacket.decode(data)
            if message.type == PacketType.MESSAGE_LOG_ADDITION:
                message_instance = Message.from_string(message.content)
                self.gui.message_box.add_message(message_instance)
            elif message.type == PacketType.MESSAGE_LOG_SET:
                log_ = JsonPacket.decode_message_log(message.content)
                self.gui.message_box.set_message_log(log_)
            elif message.type == PacketType.ERROR:
                Popup(title="Session Error", text=message.content, master=self.gui)
            elif message.type == PacketType.SUCCESS:
                Popup(title="Success", text="Success.", master=self.gui)
        except Exception as e:
            Popup(title="Client Error", text="An error has occurred with the client.", master=self.gui)
            traceback.print_exc()


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
    # For terminal usage.
    parser = argparse.ArgumentParser(
        prog="client.py",
        description="Connects to a messenger server with a GUI."
    )
    parser.add_argument('-ht', '--host', required=True)
    parser.add_argument('-p', '--port', default=STANDARD_PORT)
    args = parser.parse_args()

    log.startLogging(sys.stdout)
    reactor.connectTCP(args.host, args.port, MessagingClientFactory())
    reactor.run()
    sys.exit()
