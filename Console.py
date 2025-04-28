import datetime


class Message:
    def __init__(self, text: str, level: str, timestamp: datetime.datetime):
        self.text = text
        self.level = level
        self.timestamp = timestamp

    def get(self):
        return str(self)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f'[{self.timestamp.strftime("%H:%M:%S.%f")[:-3]}] {self.level}: {self.text}'

class Console:
    def __init__(self):
        self.messages = []

    def log(self, message: str):
        message = Message(message, 'Log', datetime.datetime.now())
        self.messages.append(message)

    def system(self, message: str):
        message = Message(message, 'System', datetime.datetime.now())
        self.messages.append(message)

    def warning(self, message: str):
        message = Message(message, 'Warning', datetime.datetime.now())
        self.messages.append(message)

    def issue(self, message: str):
        message = Message(message, 'Issue', datetime.datetime.now())
        self.messages.append(message)

    def error(self, message: str):
        message = Message(message, 'Error', datetime.datetime.now())
        self.messages.append(message)

    def getText(self):
        return '\n'.join([str(message) for message in self.messages])
