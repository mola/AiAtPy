from PySide6.QtCore import QObject, Signal

class BaseConnector(QObject):

    receivedMessage = Signal(str)

    def __init__(self):
        QObject.__init__(self)


    def send_message(self, message1, message2):
        # implement the logic to send message to the API
        pass

    def on_message_received(self, message):
        # emit the received message, it will be processed in the main app
        self.receivedMessage.emit(message)
