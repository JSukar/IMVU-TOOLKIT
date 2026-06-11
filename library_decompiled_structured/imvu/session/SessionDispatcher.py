# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.13.13 (tags/v3.13.13:01104ce, Apr  7 2026, 19:25:48) [MSC v.1944 64 bit (AMD64)]
# Embedded file name: imvu\session\SessionDispatcher.pyo
# Compiled at: 2025-11-14 17:11:18
import logging
import im.antibot
from imvu.task import ActiveObject, activemethod
from imvu.weaklist import _ref
from imvu.network import networkExceptions
from imvu.task.TaskScheduler import Return
logger = logging.getLogger('imvu.' + __name__)

class SessionDispatcher(ActiveObject):

    def __init__(self, serviceProvider, sender, avatarInfoManager):
        ActiveObject.__init__(self, serviceProvider.taskScheduler)
        self.__serviceProvider = serviceProvider
        self.__avatarInfoManager = avatarInfoManager
        self.__sender = _ref(sender)
        self.__commandManager = None
        logger.info('SessionDispatcher created')
        return

    def setCommandManager(self, c):
        logger.info('Command Manager set')
        self.__commandManager = c
        return

    @activemethod
    def participantAdded(self, userId, seat):
        logger.info('participantAdded called for %s', userId)
        sender = self.__sender()
        if sender:
            try:
                info = yield self.__avatarInfoManager.getAvatarInfo(userId)
            except networkExceptions:
                yield Return(False)
            else:
                # IMVU room antibot patch
                if im.antibot.should_boot_on_join(sender, userId, info):
                    avatar_name = getattr(info, 'avatarName', None)
                    im.antibot.try_boot_spammer(
                        sender,
                        userId,
                        'guest_spam_profile',
                        avatar_name=avatar_name,
                        event_bus=self.__serviceProvider.eventBus,
                    )
                    yield Return(False)
                self.__serviceProvider.eventBus.fire(sender, 'ParticipantJoined', {'userId': userId, 'avatarInfo': info, 'seat': seat})

        yield Return(True)
        return

    @activemethod
    def participantLeft(self, userId):
        logger.info('participantLeft called for %s', userId)
        sender = self.__sender()
        if sender:
            self.__serviceProvider.eventBus.fire(sender, 'ParticipantLeft', {'userId': userId})
        return

    @activemethod
    def notifyNewMessage(self, messageObject):
        logger.info('notifyNewMessage called for %s', repr(messageObject)[:250])
        self.synchronous_notifyNewMessage(messageObject)
        return

    def synchronous_notifyNewMessage(self, messageObject):
        sender = self.__sender()
        if self.__commandManager and sender and sender.active:
            self.__commandManager.notifyNewMessage(messageObject)
        return

    @activemethod
    def notifyMessageDelivered(self, outgoingMessageId):
        logger.info('notifyMessageDelivered called for outgoingMessageId %r', outgoingMessageId)
        self.synchronous_notifyMessageDelivered(outgoingMessageId)
        return

    def synchronous_notifyMessageDelivered(self, outgoingMessageId):
        sender = self.__sender()
        if self.__commandManager and sender and sender.active:
            self.__commandManager.notifyMessageDelivered(outgoingMessageId)
        return

    def dispose(self):
        self.stopAttachedTasks()
        return


return
