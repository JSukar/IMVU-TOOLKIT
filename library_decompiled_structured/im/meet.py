# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.13.13 (tags/v3.13.13:01104ce, Apr  7 2026, 19:25:48) [MSC v.1944 64 bit (AMD64)]
# Embedded file name: im\meet.pyo
# Compiled at: 2026-04-06 13:08:30
import logging, xmlrpclib, json
from im import session
from imvu.task import task, Start, Sleep, Event, WaitForEvent, TaskTimeout, Return, Queue as TaskQueue, Semaphore, TaskOwner, RunUntilComplete, ActiveObject
from imvu.imq.MQManager import MQListener
from imvu.imq.imqconnection import IMQError
import imvu.task
from imvu.task.util import CallPeriodically, WaitWithTimeout
from imvu.version import __version__
import imvu.network
from imvu.network import networkExceptions
from imvu import weakmethod
from imvu.util import assertInRelease
import im.common
import im.antibot
from imvu.session import SessionDispatcher
import imvu.fs, imvu.gateway, imvu.gateway.AvatarInfoManager
from imvu.session import LocalChat
from imvu.translation import LString

def NullFunc(*args, **kwargs):
    return


logger = logging.getLogger('imvu.' + __name__)
NetworkErrorRetryInterval = 10
ERROR_CHAT_FULL = 14
ERROR_CHAT_EMPTY = 15
ERROR_CHAT_NOT_PUBLIC = 16
ERROR_PUBLIC_ROOM_CLIENT_VERSION_OLD = 1
ERROR_PUBLIC_ROOM_AGE_LIMIT = 2
ERROR_PUBLIC_ROOM_CLOSED = 3
ERROR_PUBLIC_ROOM_BOOTED = 4
ERROR_PUBLIC_ROOM_FULL = 5
ERROR_OUTFIT_TOO_ADULT = 15
ERROR_NO_TEENS_ALLOWED = 16
ERROR_NO_ADULTS_ALLOWED = 17

class InvitationDeclinedDialog(object):
    uri = 'chrome://imvu/content/dialogs/input/index.html'
    size = (496, 247)
    title = 'Invitation Declined'
    geckoListeners = []


class DirectConnectSession(im.session.ImSession, TaskOwner, MQListener):
    MaxSecondsToWaitForAccept = 60

    def __init__(self, serviceProvider, userAccount, showMessageFunc=NullFunc, parentHwnd=None, dispatcherFactory=SessionDispatcher, location=None):
        im.session.ImSession.__init__(self)
        TaskOwner.__init__(self, serviceProvider.taskScheduler)
        self.activity = 'DirectConnect'
        self.__dispatcher = serviceProvider.create(dispatcherFactory, sender=self)
        self.__outgoingMessages = TaskQueue()
        self.__cancelledMessages = []
        self.__nextOutgoingMessageId = 0
        self.__location = location
        self.__isConnected = False
        self.__inviteToChatLock = Semaphore(1)
        self.__chatConnectedEvent = Event()
        self.chatId_ = None
        self.__userAccount = userAccount
        self.participants_ = []
        self.__pendingMessages = []
        self.__active = True
        self.showMessageFuncWr_ = weakmethod.ref(showMessageFunc)
        self._updateParticipantEvent = Event()
        self.__serviceProvider = serviceProvider
        self.__parentHwnd = parentHwnd
        self.__ignoredUsers = []
        self.__is_running_ = False
        self.__avatarInfoManager = imvu.gateway.AvatarInfoManager(self.__serviceProvider)
        self.waitingScale_ = 5
        self._log('creating new session')
        self.__inviteAttempts = 0
        self.__queueName = None
        self.__lastServerContact = 0
        self.__participantUrl = None
        self.__participantInfo = {}
        self.__infoUpdateQueue = []
        self.__processingParticipantInfoQueue = False
        self.__sawPureUser = False
        self.__account = None
        self.__unsentParticipantChanges = {}
        self.attachTask(CallPeriodically(self.__checkDisconnection, 5, immediatelyCall=True))
        return

    def setLocation(self, roomPid):
        self.__location = roomPid
        return

    @property
    def userId_(self):
        return self.__userAccount.getUserId()

    @property
    def location(self):
        return self.__location

    @property
    def queueName(self):
        return self.__queueName

    def updateParticipantInfo(self, account, updates, force=False):
        if account:
            self.__account = account
        if not self.__account or not (self.__account.shouldAlwaysPostToChatParticipantEndPoint() or self.__account.shouldPostToChatParticipantEndPointIfPureUserPresent() or self.__account.shouldPostToChatParticipantEndPointIfOutfitChanged()):
            return
        self.__infoUpdateQueue.insert(len(self.__infoUpdateQueue), (updates, force))
        if self.__participantUrl != None and not self.__processingParticipantInfoQueue:
            self.__processingParticipantInfoQueue = True
            self.attachTask(self.__processParticipantInfoQueue())
        return

    def __triggerParticipantUpdate(self, account=None):
        if self.__unsentParticipantChanges:
            self.updateParticipantInfo(account, self.__unsentParticipantChanges)
            self.__unsentParticipantChanges = {}
        return

    def sawPureUser(self, account):
        if not self.__sawPureUser and account.shouldPostToChatParticipantEndPointIfPureUserPresent():
            self.__sawPureUser = True
            self.__triggerParticipantUpdate(account)
        return

    @task
    def __processParticipantInfoQueue(self):
        while len(self.__infoUpdateQueue) > 0:
            changes = {}
            queue = self.__infoUpdateQueue[:]
            self.__infoUpdateQueue = []
            for updates, force in queue:
                for key in updates.keys():
                    if force or self.__participantInfo.get(key, None) != updates[key]:
                        changes[key] = updates[key]

            if not (changes and self.participants_ and (self.__account.shouldAlwaysPostToChatParticipantEndPoint() or self.__account.shouldPostToChatParticipantEndPointIfPureUserPresent() and self.__sawPureUser or self.__account.shouldPostToChatParticipantEndPointIfOutfitChanged() and changes.get('legacy_outfit_message', False))):
                self.__unsentParticipantChanges.update(changes)
                break
            self.__participantInfo.update(changes)
            logger.info('NRD POSTing to chat_participant endpoint: %r', changes)
            try:
                yield imvu.http.securePost(url=self.__participantUrl, params=changes, auth=self.__account.getAuth(), responseSchema=[], network=self.__serviceProvider.network, method='POST')
            except networkExceptions:
                pass

        self.__processingParticipantInfoQueue = False
        return

    def _log(self, message, *args):
        logger.info((message + ' session=%r'), *(args + (self,)))
        return

    def getChatId(self):
        return self.chatId_

    def isOwner(self, userId):
        return self.userId_ == userId

    @property
    def active(self):
        return self.__active

    def __repr__(self):
        return '<%s %s: instance %s, userId %s, chat %s>' % (
         type(self).__name__,
         self.activity,
         self._instanceId,
         self.userId_,
         self.chatId_)

    @task
    @staticmethod
    def __reportChatTermination(chatGateway, userId, chatId):
        if not chatId:
            return
        try:
            yield chatGateway.terminateChat(userId, chatId)
        except networkExceptions:
            logger.exception('chatGateway.terminateChat(%r, %r) failed', userId, chatId)

        return

    def closeSession(self):
        self._log('closeSession')
        self.__serviceProvider.taskScheduler.scheduleTask(self.__reportChatTermination(self.__serviceProvider.chatGateway, self.userId_, self.chatId_), executionPolicy=RunUntilComplete)
        self.__markClosed()
        return

    def __markClosed(self):
        self._log('__markClosed')
        self.stopAttachedTasks()
        self.__dispatcher.dispose()
        self.__active = False
        return

    def isConnected(self):
        return self.__isConnected

    def __checkDisconnection(self):
        if self.__isConnected and self.__serviceProvider.timeProvider() - self.__lastServerContact > 180:
            logger.info('Detected disconnection, last server contact at %d, it is now %d', self.__lastServerContact, self.__serviceProvider.timeProvider())
            self.__serviceProvider.eventBus.fire(self, 'DisconnectionDetected', {})
        return

    def maybeConnect(self, private=None):
        if self.__isConnected or self.__is_running_:
            return
        self._log('maybeConnect decided to connect')
        self.__is_running_ = True

        @task
        def initialize():
            connected = yield self.__connectToChat(private=private)
            if connected:
                self.__setupPostConnectTasks()
            return

        self.attachTask(initialize())
        return

    def __setupPostConnectTasks(self):
        self.__isConnected = self.chatId_ is not None
        if self.isConnected():
            self.attachTask(self._sendOutgoingMessages())
            self.attachTask(self._updateParticipantList())
        return

    def _showUiMessage(self, messageText, timeout=3):
        msgFunc = self.showMessageFuncWr_()
        if msgFunc:
            return msgFunc(sess=self, messageText=messageText, timeout=timeout)
        return

    def _showConnectedMessage(self):
        return

    def getParticipantUserIds(self):
        return sorted(set([self.userId_] + self.participants_))

    @task
    def __handleWaitingResult(self, result):
        self._showStillWaitingMsg()
        logger.debug('%s(userId=%s)::getOrMakeChat returned waiting result: %s', self, self.userId_, result)
        try:
            self.chatId_ = result['chatId']
            self.__chatConnectedEvent.set()
        except KeyError:
            pass
        else:
            self.__serviceProvider.eventBus.fire(self, 'NewChatId', {'chatId': (self.chatId_)})

        yield Sleep(0.5 + self.waitingScale_ * 0.5)
        return

    @task
    def __joinChat(self, chatId, seat=None):
        self.chatId_ = chatId
        self.__chatConnectedEvent.set()
        self.__serviceProvider.eventBus.fire(self, 'JoinedChat', {'chatId': (self.chatId_), 'seat': seat})
        self.__serviceProvider.eventBus.fire(self, 'NewChatId', {'chatId': (self.chatId_)})
        im.antibot.clear_boot_log(self)
        im.antibot.publish_protection_status(self, self.__serviceProvider.eventBus)
        self.__queueName = '/chat/%i' % int(self.chatId_)

        @task
        def joinImqChat():
            if not self.__serviceProvider.mqManager.isConnected():
                yield self.__serviceProvider.mqManager.reconnect()
            yield self.__serviceProvider.mqManager.subscribe(self.__queueName, self, {'listen_to_self': False})
            return

        yield WaitWithTimeout(joinImqChat(), 20.0)
        self._log('joined chat queue %s', self.__queueName)
        if seat is not None:
            self.sendImMessage(messageText='*seat %s' % seat)
            if seat == 1:
                self.sendImMessage(messageText='*resume %s' % self.userId_)
            else:
                self.sendImMessage(messageText='*accept %s' % self.userId_)
        self._log('__joinChat connected to chat %s', self.chatId_)
        self._showConnectedMessage()
        self.__lastServerContact = self.__serviceProvider.timeProvider()
        return

    @task
    def __connectToChat(self, private=None):
        attempts = 0
        inviteId = None
        connected = True
        while True:
            if attempts == 5:
                self.__serviceProvider.eventBus.fire(self, 'ChatConnectFailed')
                connected = False
                break
            try:
                result = yield self.getOrMakeChat(inviteId=inviteId, private=private)
            except networkExceptions:
                logger.exception('failed getOrMakeChat for userId %s, retrying', self.userId_)
                attempts += 1
                yield Sleep((0.5 + self.waitingScale_ * 0.5) * attempts)
                continue

            if result is None or isinstance(result, str):
                attempts += 1
                yield Sleep((0.5 + self.waitingScale_ * 0.5) * attempts)
                continue
            self._log('getOrMakeChat result: %s', result)
            if result.get('response', 'accepted') == 'declined' or result.get('response', 'accepted') == 'timeout':
                break
            self.__participantUrl = result.get('participantUrl')
            if result.get('waiting', False):
                yield self.__handleWaitingResult(result)
                inviteId = result.get('inviteId', None)
                continue
            try:
                yield self.__joinChat(result['chatId'], result.get('seat'))
            except (IMQError, TaskTimeout) as e:
                self._log('error joining chat queue: %r', e)
                self.__serviceProvider.eventBus.fire(self, 'ChatConnectFailed')
                connected = False

            break

        yield Return(connected)
        return

    def __handleRejoinChatError(self):
        self.closeSession()
        title = self.__serviceProvider.translationTable.LS('Sorry!')
        text = self.__serviceProvider.translationTable.LS('You are no longer in the chat.')
        self.__serviceProvider.dialogManager.showModal(self.__parentHwnd, imvu.dialog.ConfirmationDialog(title, text))
        self.endSession()
        return

    def __showUnsentMessage(self, msg):
        if not msg.startswith('*'):
            self._showUiMessage(self.__serviceProvider.translationTable.FLS('Message was not sent: {0!r}', msg))
            return True
        return False

    def __isCancelled(self, outgoingMessageId):
        return outgoingMessageId in self.__cancelledMessages

    def __notifyOutgoingMessageDelivered(self, outgoingMessageId):
        self.__cancelledMessages = filter((lambda messageId: messageId > outgoingMessageId), self.__cancelledMessages)
        self.__dispatcher.notifyMessageDelivered(outgoingMessageId)
        return

    @task
    def flushMessages(self, messages):
        while not self.__outgoingMessages.empty():
            messages.append((yield self.__outgoingMessages.get()))

        if not messages:
            return
        else:
            self._log('flushMessages dequeued messages %r', messages)

            def formatMessage((msg, to, outgoingMessageId)):
                return ({'userId': (self.userId_), 'chatId': (self.chatId_), 'message': msg, 'to': to}, outgoingMessageId)

            formattedMessages = map(formatMessage, messages)
            if not formattedMessages:
                return

            @task
            def ensureJoinedChat():
                if not self.__serviceProvider.mqManager.isConnected():
                    yield self.__serviceProvider.mqManager.waitForConnection()
                try:
                    yield WaitWithTimeout(self.__serviceProvider.mqManager.waitForSubscription(self.__queueName), 20.0)
                except (IMQError, TaskTimeout) as e:
                    self._log('failed to resubscribe to chat queue after reconnecting to IMQ: %r', e)
                    self.__handleRejoinChatError()

                return

            for msg, outgoingMessageId in formattedMessages:
                jsonMsg = json.dumps(msg)
                logger.debug('send IMQ chat message: %s', jsonMsg)
                yield ensureJoinedChat()
                if outgoingMessageId != None and self.__isCancelled(outgoingMessageId):
                    self._log('not sending cancelled message %r', msg)
                    continue
                try:
                    if outgoingMessageId != None:
                        self.__notifyOutgoingMessageDelivered(outgoingMessageId)
                    yield self.__serviceProvider.mqManager.sendMessage(jsonMsg, self.__queueName, 'messages')
                except IMQError as e:
                    self._log('failed to send message %r to imq: %r', jsonMsg, e)
                    self.__showUnsentMessage(msg['message'])

            return

    @task
    def _sendOutgoingMessages(self):
        self._log('Starting outgoing message loop')
        while True:
            yield self.flushMessages(messages=[(yield self.__outgoingMessages.get())])

        return

    @task
    def _updateParticipantList(self):
        self._log('Starting participant update loop')
        try:
            while True:
                if not self.__serviceProvider.mqManager.isConnected():
                    yield self.__serviceProvider.mqManager.waitForConnection()
                    try:
                        yield WaitWithTimeout(self.__serviceProvider.mqManager.waitForSubscription(self.__queueName), 20.0)
                    except (TaskTimeout, IMQError) as e:
                        self._log('error rejoining chat queue in _updateParticipantList: %r', e)
                        break

                try:
                    participantInfos = yield self.__serviceProvider.chatGateway.getParticipants(self.userId_, self.chatId_)
                except networkExceptions:
                    logger.exception('error trying to find participants for chat %s', self.chatId_)
                else:
                    participantsChanged = False
                    self.__lastServerContact = self.__serviceProvider.timeProvider()
                    seats = {}
                    newParticipants = set()
                    for p in participantInfos:
                        userId = int(p['userId'])
                        seats[userId] = p['seat']
                        newParticipants.add(userId)

                    for userId in set(self.participants_) - newParticipants:
                        self._log('notifyParticipantRemoved(): userId: %r', userId)
                        self.participants_.remove(userId)
                        participantsChanged = True
                        yield self.__dispatcher.participantLeft(userId)

                    for userId in newParticipants - set(self.participants_):
                        self.participants_.append(userId)
                        participantsChanged = True
                        gotInfo = yield self.__dispatcher.participantAdded(userId, seats[userId])
                        if not gotInfo:
                            self.participants_.remove(userId)

                    for message_dict in self.__pendingMessages:
                        if message_dict['from_id'] in self.participants_:
                            self.__processIncomingMessage(message_dict)
                        else:
                            logger.warning('Ignoring message %r because user is not in chat', message_dict)

                    del self.__pendingMessages[:]
                    if self.numParticipants() == 1 and self.isRoomSession():
                        self.__outgoingMessages.put(('*uid %d' % self.userId_, 0, None))
                    if participantsChanged:
                        self.__serviceProvider.eventBus.fire(self, 'ParticipantsUpdated')
                        self.__triggerParticipantUpdate()
                    self._updateParticipantEvent.clear()
                    try:
                        yield WaitForEvent(self._updateParticipantEvent, 14.5)
                    except TaskTimeout:
                        pass

        finally:
            self._log('Exiting update participant loop')

        return

    def _partnerLeftDialogCallback(self, ignore):
        self._log('_partnerLeftDialogCallback numParticipants_ is %s', self.numParticipants())
        if self.numParticipants() <= 1 and not self.isRoomSession():
            self.endSession()
        return

    def ignoreUser(self, userId):
        self.__ignoredUsers.append(userId)
        return

    def unIgnoreUser(self, userId):
        self.__ignoredUsers.remove(userId)
        return

    def isIgnoredUser(self, userId):
        return userId in self.__ignoredUsers

    def __addIncomingMessage(self, messageDict):
        assertInRelease(messageDict)
        from_id = int(messageDict['from_id'])
        if from_id != 0:
            if self.isIgnoredUser(from_id):
                return
            # IMVU room antibot patch
            block, reason = im.antibot.check_incoming_message(self, from_id, messageDict)
            if block:
                im.antibot.try_boot_spammer(
                    self,
                    from_id,
                    reason,
                    event_bus=self.__serviceProvider.eventBus,
                )
                return
            if from_id not in self.getParticipantUserIds():
                self._log('Deferring message %r, updating participant list', messageDict)
                self.__pendingMessages.append(messageDict)
                self._updateParticipantEvent.set()
                return
        self.__processIncomingMessage(messageDict)
        return

    def __processIncomingMessage(self, messageDict):
        from_id = int(messageDict.get('from_id', 0))
        if from_id and im.antibot.is_promo_message(messageDict.get('message', '')):
            if im.antibot.try_boot_spammer(
                self,
                from_id,
                'promo_message',
                event_bus=self.__serviceProvider.eventBus,
            ):
                return
        self.__dispatcher.notifyNewMessage(im.common.ImMessage(message=messageDict.get('message', ''), timestamp=self.__serviceProvider.timeProvider(), fromId=int(messageDict.get('from_id', 0)), toId=int(messageDict.get('to_id', 0)), outgoingMessageId=messageDict['outgoing_id'] if 'outgoing_id' in messageDict else None))
        return

    def endSession(self):
        self.__serviceProvider.eventBus.fire(self, 'Session.End')
        return

    def sendImMessage(self, messageText, to=0):
        self._log('sendImMessage(): messageText: %r', messageText)
        self.maybeConnect()
        outgoingMessageId = self.__nextOutgoingMessageId
        self.__nextOutgoingMessageId += 1
        self.__outgoingMessages.put((messageText, to, outgoingMessageId))
        self.__addIncomingMessage({'from_id': (self.userId_), 'message': messageText, 'to_id': to, 'outgoing_id': outgoingMessageId})
        return outgoingMessageId

    def cancelMessage(self, outgoingMessageId):
        assertInRelease(type(outgoingMessageId) == int)
        self.__cancelledMessages.append(outgoingMessageId)
        return

    def setCommandManager(self, c):
        self.__dispatcher.setCommandManager(c)
        return

    def numParticipants(self):
        return len(self.getParticipantUserIds())

    def sessionIsFull(self):
        return False

    def isPrivate(self):
        return False

    @task
    def _sendInvitation(self, partnerId, inviteId=None):
        if partnerId == self.userId_:
            yield Return({'response': 'decline', 'reason': 'You cannot invite yourself to a chat'})
        yield self.__chatConnectedEvent.wait()
        args = {'userId': (self.userId_), 
           'partnerId': partnerId, 
           'chatId': (self.chatId_ or 0), 
           'location': (self.location)}
        if inviteId is not None:
            args['inviteId'] = inviteId
        rv = yield self.__serviceProvider.chatGateway.attemptInvite(**args)
        yield Return(rv)
        return

    def inviteToChat(self, inviteeId):
        self.attachTask(self.__inviteToChat(inviteeId))
        return

    @task
    def sendAwayNote(self, inviteId, inviteeId, reason):
        self._log('sendAwayNote(): inviteId: %r inviteeId: %r reason: %r', inviteId, inviteeId, reason)
        reason = reason[10:]
        partnerName = yield self.__serviceProvider.avatarInfoManager.getAvatarName(inviteeId)
        dialog = InvitationDeclinedDialog()
        dialog.dialogInfo = {'title': (LString('Invitation declined')), 
           'message': (self.__serviceProvider.translationTable.FLS('{avatarname} is currently: ', avatarname=partnerName) + self.__serviceProvider.translationTable.FLS('{awayMessage!r}.  Would you like to leave a note?', awayMessage=reason if reason else '')), 
           'defaultValue': ''}
        user_message = self.__serviceProvider.dialogManager.showModal(self.__parentHwnd, dialog)
        if not user_message:
            return
        user_name = yield self.__serviceProvider.avatarInfoManager.getAvatarName(self.userId_)
        if not user_name:
            user_name = '<Avatar>'
        away_note = user_name + ':  ' + user_message
        yield self.__serviceProvider.chatGateway.leaveInviteAwayNote(self.userId_, inviteId, away_note)
        return

    @task
    def __inviteToChat(self, inviteeId):
        with (yield self.__inviteToChatLock.acquire()):
            firstInviteAttemptTime = self.__serviceProvider.timeProvider()
            self._log('inviteToChat(%s, %s) firstInviteAttemptTime=%d', self, inviteeId, firstInviteAttemptTime)
            self.__inviteAttempts = 0
            self._showStillWaitingMsg()
            inviteId = None
            while True:
                self.__inviteAttempts += 1
                logger.info('inviteToChat attempting to make invite #%d (time is %d)', self.__inviteAttempts, self.__serviceProvider.timeProvider())
                try:
                    ret = yield self._sendInvitation(partnerId=inviteeId, inviteId=inviteId)
                except xmlrpclib.Fault as e:
                    if e.faultCode == 32:
                        ret = {'response': 'decline', 'reason': (e.faultString)}
                        if e.faultString == "Can't invite teens":
                            ret['accessViolation'] = 'adults'
                        elif e.faultString == "Can't invite adults":
                            ret['accessViolation'] = 'minors'
                        else:
                            ret['joinError'] = e.faultString
                    else:
                        logger.exception('sendInvitation raised, assuming we should keep waiting.')
                        ret = {'waiting': True}
                except networkExceptions:
                    logger.exception('sendInvitation raised, assuming we should keep waiting.')
                    ret = {'waiting': True}

                newInviteId = ret.get('inviteId')
                try:
                    newInviteId = int(newInviteId)
                except (TypeError, ValueError):
                    logger.warning('Got funky inviteId: %r', newInviteId)

                if inviteId is not None and newInviteId is not None and inviteId != newInviteId:
                    logger.critical('We asked for the status of an invite - but got back a new invite!')
                if inviteId is None:
                    inviteId = newInviteId
                if not self.chatId_ and ret.get('chatId', 0) != 0:
                    logger.info("Didn't have a chat, but got one! %r", ret['chatId'])
                    yield self.__joinChat(ret['chatId'], 1)
                    self.__setupPostConnectTasks()
                if 'waiting' in ret:
                    if self.__serviceProvider.timeProvider() - firstInviteAttemptTime > self.MaxSecondsToWaitForAccept:
                        self._log('partner %s timed out our invitation after %d seconds', inviteeId, self.__serviceProvider.timeProvider() - firstInviteAttemptTime)
                        partnerName = yield self.__serviceProvider.avatarInfoManager.getAvatarName(inviteeId)
                        self._hideStillWaitingMsg()
                        self._showUiMessage(self.__serviceProvider.translationTable.FLS('{partnerName} did not answer your invitation.', partnerName=partnerName), timeout=30)
                        return
                elif 'response' in ret:
                    response = ret['response']
                    if response == 'decline':
                        reason = ret.get('reason', None)
                        inviteId = ret.get('inviteId', None)
                        accessViolation = ret.get('accessViolation', None)
                        joinError = ret.get('joinError', None)
                        if not reason:
                            reason = 'no reason given'
                        self._log('partner %s declined our invitation, closing session', inviteeId)
                        self._hideStillWaitingMsg()
                        if reason.find("I'm away") >= 0 and inviteId:
                            self.attachTask(self.sendAwayNote(inviteId, inviteeId, reason))
                        else:
                            partnerName = yield self.__serviceProvider.avatarInfoManager.getAvatarName(inviteeId)
                            if joinError:
                                self._showUiMessage(self.__serviceProvider.translationTable.FLS(u'{partnerName} can not join because', partnerName=partnerName) + ' ' + joinError, timeout=300)
                            elif accessViolation:
                                self._showUiMessage(self.__serviceProvider.translationTable.FLS(u'{partnerName} can not join as the room only allows', partnerName=partnerName) + ' ' + accessViolation, timeout=300)
                            else:
                                self._showUiMessage(self.__serviceProvider.translationTable.FLS(u'{partnerName} declined to chat, saying', partnerName=partnerName) + " '" + reason + "'", timeout=300)
                        return
                    raise Exception('unknown response: %r' % ret)
                else:
                    self._log('inviteToChat: invite was accepted from %s', inviteeId)
                    self._updateParticipantEvent.set()
                    self._hideStillWaitingMsg()
                    return
                yield Sleep(1)

            raise Exception('should never be reached')
        return

    def onImqMessage(self, message):
        self._log('onImqMessage(%r)', [message.user_id, message.queue, message.mount, message.message])
        try:
            m = json.loads(message.message)
        except ValueError as e:
            m = None

        if message.mount == 'control':
            if not isinstance(m, dict):
                self._log('Got invalid control message %r', m)
                return
            self.__serviceProvider.eventBus.fire(self, 'ControlMessage', m)
        elif message.mount == 'messages':
            if not isinstance(m, dict):
                self._log('Got invalid chat message %r', m)
                return
            m['from_id'] = message.user_id if isinstance(message.user_id, int) else int(message.user_id.split('/')[-1])
            if m['from_id'] != m.get('userId', 0):
                self._log('forged message detected: from %r: %r', message.user_id, m)
            m['to_id'] = m.get('to', 0)
            self.__addIncomingMessage(m)
        return

    def _showStillWaitingMsg(self):
        return

    def _hideStillWaitingMsg(self):
        return

    def canBoot(self, booter, bootee):
        return False

    def isLieutenant(self, userId):
        return False


class InviteDecision():
    ACCEPT = 'ACCEPT'
    DECLINE = 'DECLINE'
    IGNORE = 'IGNORE'
    REJECTED = 'REJECTED'


class ChatSession(DirectConnectSession):

    def __init__(self, serviceProvider, userAccount, result, showMessageFunc=NullFunc, parentHwnd=None, location=0):
        DirectConnectSession.__init__(self, serviceProvider=serviceProvider, userAccount=userAccount, showMessageFunc=showMessageFunc, parentHwnd=parentHwnd, location=location)
        self.__result = result
        self.maybeConnect()
        return

    @task
    def getOrMakeChat(self, inviteId=None, private=None):
        return self.__result

    def shouldResetRoomDefinitionAtStartup(self):
        return False


DEFAULT_PUBLIC_ROOM_TITLE = 'IMVU Chat Room'

class JoinRoomSession(DirectConnectSession):

    def __init__(self, roomInstanceId, serviceProvider, userAccount, modeConstructedEvent, showMessageFunc=NullFunc, parentHwnd=None, lieutenants=[], roomOwners=[], allowRoomShellOverwrite=False, allowLoadNewRoom=False, private=None, autoBootWhenOwnerLeaves=True):
        DirectConnectSession.__init__(self, serviceProvider=serviceProvider, userAccount=userAccount, showMessageFunc=showMessageFunc, parentHwnd=parentHwnd)
        if not isinstance(roomInstanceId, basestring):
            raise TypeError('roomInstanceId must be a string, was %r' % (roomInstanceId,))
        if not isinstance(roomOwners, list):
            raise TypeError('roomOwners must be a list, was %r' % (roomOwners,))
        self.roomInstanceId_ = roomInstanceId
        self.__serviceProvider = serviceProvider
        self.__modeConstructedEvent = modeConstructedEvent
        self.__lieutenants = lieutenants
        self.__roomOwners = roomOwners
        self.__allowRoomShellOverwrite = allowRoomShellOverwrite
        self.__allowLoadNewRoom = allowLoadNewRoom
        self.__parentHwnd = parentHwnd
        self.__private = private
        self.__autoBootWhenOwnerLeaves = autoBootWhenOwnerLeaves
        self.reasons_ = {ERROR_PUBLIC_ROOM_CLIENT_VERSION_OLD: (self.__serviceProvider.translationTable.LS('Your client version is too old, please upgrade to the latest version.')), 
           ERROR_PUBLIC_ROOM_AGE_LIMIT: (self.__serviceProvider.translationTable.LS('You are too young to join a chat room chat.')), 
           ERROR_PUBLIC_ROOM_CLOSED: (self.__serviceProvider.translationTable.LS('The room is currently closed.')), 
           ERROR_PUBLIC_ROOM_BOOTED: (self.__serviceProvider.translationTable.LS('You have been kicked out of the room.  Cannot rejoin within 20 minutes.')), 
           ERROR_PUBLIC_ROOM_FULL: (self.__serviceProvider.translationTable.LS('The room is full.')), 
           ERROR_OUTFIT_TOO_ADULT: (self.__serviceProvider.translationTable.LS('Your outfit has products you cannot wear into that room. Please try a more generally acceptable outfit.')), 
           ERROR_NO_TEENS_ALLOWED: (self.__serviceProvider.translationTable.LS('You cannot enter a chat room hosted by an adult.')), 
           ERROR_NO_ADULTS_ALLOWED: (self.__serviceProvider.translationTable.LS('You cannot enter a chat room hosted by a minor.'))}
        self.maybeConnect(private=private)
        return

    @property
    def location(self):
        return self.roomInstanceId_

    def isOwner(self, userId):
        return self.roomInstanceId_.startswith(str(userId) + '-') or userId in self.getRoomOwners()

    def isPrivate(self):
        return self.__private

    def getOwner(self):
        return int(self.roomInstanceId_.split('-')[0])

    def isLieutenant(self, userId):
        return str(userId) in self.__lieutenants

    def hasBootPrivileges(self, userId):
        return self.isOwner(userId) or self.isLieutenant(userId)

    def canBoot(self, booter, bootee):
        return self.hasBootPrivileges(booter) and not self.hasBootPrivileges(bootee)

    def isRoomSession(self):
        return True

    def allowRoomShellOverwrite(self):
        return self.__allowRoomShellOverwrite

    def autoBootWhenOwnerLeaves(self):
        return self.__autoBootWhenOwnerLeaves

    def setAutoBootWhenOwnerLeaves(self, autoBootWhenOwnerLeaves):
        self.__autoBootWhenOwnerLeaves = autoBootWhenOwnerLeaves
        return

    def allowLoadNewRoom(self):
        return self.__allowLoadNewRoom

    def getRoomOwners(self):
        return self.__roomOwners

    def setRoomOwners(self, roomOwners):
        self.__roomOwners = roomOwners
        return

    def setLieutenants(self, lieutenants):
        self.__lieutenants = lieutenants
        return

    def isAlwaysDriver(self):
        return False

    def resetRoomDefinitionAtStartup(self):
        return False

    def getRoomInstanceId(self):
        return self.roomInstanceId_

    def setRoomInstanceId(self, roomInstanceId):
        self.roomInstanceId_ = roomInstanceId
        return

    @task
    def getOrMakeChat(self, inviteId=None, private=None):
        self._log('JoinRoomSession::getOrMakeChat(): self.userId_: %r self.roomInstanceId_: %r', self.userId_, self.roomInstanceId_)
        activity = 'publicroom-%s' % self.roomInstanceId_
        ret = yield self.__serviceProvider.chatGateway.getOrMakeChat(self.userId_, activity, self.chatId_ or 0, publicRoom=True, private=private)
        if 'response' in ret and ret['response'] == 'declined':
            errorCode = ret.get('reason', None)
            errorExplanation = ret.get('explanation', None)
            self._log('User %s declined to join the chat room, closing session', self.userId_)
            yield self.__modeConstructedEvent.wait()
            self.closeSession()
            self.__showErrorMessage(errorCode, errorExplanation)
        else:
            yield Return(ret)
        return

    def bootUser(self, userId):
        self._log('boot user %r', userId)

        @task
        def boot():
            yield self.__serviceProvider.chatGateway.bootOutOfChat({'userId': userId, 
               'roomInstanceId': (self.roomInstanceId_)})
            self._updateParticipantEvent.set()
            return

        self.attachTask(boot())
        return

    def __showErrorMessage(self, errorCode, errorExplanation):
        if errorCode is None:
            return
        else:
            if errorCode == ERROR_PUBLIC_ROOM_FULL:
                title = self.__serviceProvider.translationTable.LS('Sorry!')
                text = self.__serviceProvider.translationTable.LS('Looks like this chat room is quite popular and appears to be full! Be sure to visit other rooms and come back here later...')
            elif errorExplanation is None:
                reason = self.reasons_.get(int(errorCode), 'no reason given')
                title = self.__serviceProvider.translationTable.LS('Chat Room Access Declined')
                text = self.__serviceProvider.translationTable.FLS('Your access to the chat room is declined. Reason: {0!r}', reason)
            else:
                title = self.__serviceProvider.translationTable.LS('Chat Room Access Declined')
                text = self.__serviceProvider.translationTable.FLS('{0}', errorExplanation)
            self.__serviceProvider.dialogManager.showModal(self.__parentHwnd, imvu.dialog.ConfirmationDialog(title, text))
            self.endSession()
            return

    def _showStillWaitingMsg(self):
        self._showUiMessage(self.__serviceProvider.translationTable.LS('Inviting: waiting for reply...'))
        return


@task
def handleInvite(serviceProvider, userId, decisionCallback, startChatCallback, parentHwnd=None):

    class IMQInviteReceiver(object):

        def __init__(self):
            self.__future = None
            serviceProvider.eventBus.register(serviceProvider.serverEventTransport, 'ServerEvent.chatInvite', self.__inviteReceived)
            return

        def __inviteReceived(self, event):
            if self.__future:
                future = self.__future
                self.__future = None
                future.complete(event.info)
            return

        @property
        def future(self):
            self.__future = imvu.task.Future()
            return self.__future

    logger.info('listening for IMQ chat invites')
    receiver = IMQInviteReceiver()
    while True:
        invite = yield receiver.future
        yield _handleInvite(serviceProvider, invite, userId, decisionCallback, startChatCallback, parentHwnd)

    return


@task
def _handleInvite(serviceProvider, invite, userId, decisionCallback, startChatCallback, parentHwnd):
    if not (type(invite) is dict and all(key in invite for key in ('chatId', 'inviteId',
                                                                   'partnerId', 'location',
                                                                   'inviter'))):
        logger.error('ignoring invite (%r)', invite)
        return
    chatId = invite['chatId']
    inviteId = invite['inviteId']
    partnerId = invite['partnerId']
    location = invite['location']
    partnerData = invite['inviter']
    decision, reason = yield decisionCallback(partnerId, location, partnerData)
    if decision is InviteDecision.ACCEPT:
        logger.info('Accepting chat invitation')
        try:
            result = yield serviceProvider.chatGateway.acceptInvite({'userId': userId, 
               'inviteId': inviteId, 
               'chatId': chatId})
            if result.get('expired'):
                message = serviceProvider.translationTable.LS('Sorry, the invite has expired and the room is unavailable')
                title = serviceProvider.translationTable.LS('Invite Has Expired')
                serviceProvider.dialogManager.showModal(parentHwnd, imvu.dialog.ConfirmationDialog(title, message))
                yield Return(False)
            participantInfos = yield serviceProvider.chatGateway.getParticipants(userId, chatId)
            result['location'] = location
        except networkExceptions:
            logger.exception('acceptInvite failed')
        else:
            logger.info('acceptInvite returned %s', result)
            participants = [int(x['userId']) for x in participantInfos]
            if partnerId in participants:
                startChatCallback(partnerId, result)
            else:
                name = yield serviceProvider.avatarInfoManager.getAvatarName(partnerId)
            message = serviceProvider.translationTable.FLS('Oops, {0} has left the chat', name)
            title = serviceProvider.translationTable.LS('Chat Ended')
            serviceProvider.dialogManager.showModal(parentHwnd, imvu.dialog.ConfirmationDialog(title, message))

    elif decision is InviteDecision.DECLINE or decision is InviteDecision.REJECTED:
        logger.info('Declining chat invitation')
        try:
            yield serviceProvider.chatGateway.declineInvite({'userId': userId, 'inviteId': inviteId, 
               'reason': reason, 
               'chatId': chatId, 
               'status': ('rejected' if decision is InviteDecision.REJECTED else 'declined')})
        except networkExceptions:
            logger.exception('declineInvite failed')

    return


@task
def checkInviteSafety(serviceProvider, userId, roomPid, contents):
    try:
        avatarInfo = yield serviceProvider.avatarInfoManager.getAvatarInfo(userId)
    except Exception as e:
        yield Return()

    if not avatarInfo.hasAP:
        productInfo, = yield serviceProvider.productInfoManager.getProductsByIds([roomPid])
        if productInfo.requiresAP:
            yield Return('You can not invite a non-AP user to an AP room.')
    if not avatarInfo.hasAPPlus:
        pidlist = [c[1][0] for c in contents.iteritems()]
        pidlist.append(roomPid)
        productInfos = yield serviceProvider.productInfoManager.getProductsByIds(pidlist)
        for productInfo in productInfos:
            if productInfo.requiresAPPlus:
                yield Return('You can not invite a non-AP+ user to an AP+ room.')

    return


class MeetSomeoneSession(DirectConnectSession):

    def __init__(self, serviceProvider, userAccount, roomInstanceId, showMessageFunc=NullFunc, parentHwnd=None):
        DirectConnectSession.__init__(self, serviceProvider=serviceProvider, userAccount=userAccount, showMessageFunc=showMessageFunc, parentHwnd=parentHwnd)
        self.__serviceProvider = serviceProvider
        self.__roomInstanceId = roomInstanceId
        self.__chatNowParams_ = {}
        self.__avatarInfoManager = imvu.gateway.AvatarInfoManager(self.__serviceProvider)
        self.__parentHwnd = parentHwnd
        self.maybeConnect(private=True)
        return

    @property
    def __participantId(self):
        if self.participants_:
            return self.participants_[0]
        else:
            return
            return

    def getActivity(self):
        return 'Chat now-' + self.__roomInstanceId

    def getRoomInstanceId(self):
        return self.__roomInstanceId

    def getOwner(self):
        return self.userId_

    def setChatNowParams(self, chatParams):

        def filter(collection, filters):
            return dict((key, value) for key, value in chatParams.iteritems() if key in filters)

        self.__chatNowParams_ = filter(chatParams, [2, 3, 4, 5, 6])
        return

    def _getChatNowParams(self):
        return self.__chatNowParams_

    def isRoomSession(self):
        return True

    @task
    def getOrMakeChat(self, inviteId=None, private=None):
        filter = self.__chatNowParams_.get('filter', 'surprise')
        activity = 'Chat now-' + filter
        args = {'userId': (self.userId_), 'version': __version__, 
           'activity': activity, 
           'chatId': (self.chatId_ or 0), 
           'private': (private or True), 
           'chatNowParams': (self.__chatNowParams_)}
        try:
            result = yield self.__serviceProvider.chatGateway.getOrMakeChat(self.userId_, activity, self.chatId_ or 0, publicRoom=None, private=None, chatNowParams=self.__chatNowParams_ or None)
        except networkExceptions as e:
            logger.warning('Ignoring networkExceptions error in MeetSomeoneSession.getOrMakeChat: %r', e)
            result = None

        yield Return(result)
        return

    def _showStillWaitingMsg(self):
        self._log('MeetSomeoneSession: _showStillWaitingMsg')
        self._showUiMessage(self.__serviceProvider.translationTable.LS('Connecting you with another person...'), 2)
        return

    def _showConnectedMessage(self):
        self._showUiMessage(self.__serviceProvider.translationTable.LS('Chat now! found someone...'))
        return

