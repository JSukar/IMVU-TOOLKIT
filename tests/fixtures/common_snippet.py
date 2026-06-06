class ImMessage(object):
    def __init__(self, message):
        if isinstance(message, str):
            self.__message = message
        else:
            self.__message = message.decode('windows-1252')
