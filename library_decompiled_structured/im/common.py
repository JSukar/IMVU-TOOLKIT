# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.8.10 (tags/v3.8.10:3d8993a, May  3 2021, 11:48:03) [MSC v.1928 64 bit (AMD64)]
# Embedded file name: im\common.pyo
# Compiled at: 2025-11-14 17:11:17
import sys, types, logging
from imvu.util import assertInRelease

class ImMessage(object):

    def __init__(self, message, timestamp, fromId, toId=0, isMacroExpansionMsg=False, outgoingMessageId=None):
        assertInRelease(message is not None)
        if type(message) is str:
            # IMVU emoji/unicode patch: prefer UTF-8, fall back to legacy chat encoding.
            try:
                self.__message = message.decode('utf-8')
            except UnicodeDecodeError:
                self.__message = message.decode('windows-1252', 'replace')
        else:
            self.__message = unicode(message)
        self.timestamp_ = timestamp
        self.__fromId = fromId
        self.__toId = toId
        self.isMacroExpansionMsg_ = isMacroExpansionMsg
        self.__outgoingMessageId = outgoingMessageId
        return

    @property
    def fromId_(self):
        return self.__fromId

    @property
    def toId(self):
        return self.__toId

    @property
    def message_(self):
        return self.__message

    @property
    def outgoingMessageId(self):
        return self.__outgoingMessageId

    def __repr__(self):
        return '%s/%s/%s' % (repr(self.fromId_), repr(self.message_), repr(self.timestamp_))

    def __str__(self):
        return self.message_

    def getMessageTimestamp(self):
        return self.timestamp_

    def getMessageText(self):
        return self.message_

    def getMessageFromId(self):
        return self.fromId_


return
