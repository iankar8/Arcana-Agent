class CommunicationBus:
    def __init__(self):
        self.messages = []

    def send_message(self, message):
        self.messages.append(message)

    def receive_messages(self):
        return self.messages
