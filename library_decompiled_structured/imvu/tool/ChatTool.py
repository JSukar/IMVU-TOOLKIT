# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.13.13 (tags/v3.13.13:01104ce, Apr  7 2026, 19:25:48) [MSC v.1944 64 bit (AMD64)]
# Embedded file name: imvu\tool\ChatTool.pyo
# Compiled at: 2025-11-14 17:11:19
import logging
logger = logging.getLogger('imvu.' + __name__)
# IMVU room antibot patch hooks in ChatToolGeckoListener below.
import imvu.dialog, imvu.gecko, imvu.menu
from imvu.imq.geckolistener import IMQGeckoListener
from imvu.translation import LString
from .HtmlTool import HtmlTool

class ChatToolGeckoListener(object):
    imvuCallHandlers = imvu.gecko.HandlerList()

    def __init__(self, sessionWindow, serviceProvider, userAccount):
        self.__sessionWindow = sessionWindow
        self.__menuFactory = serviceProvider.menuFactory
        self.__platformService = serviceProvider.platform
        self.__serviceProvider = serviceProvider
        self.__userAccount = userAccount
        return

    @imvuCallHandlers.register
    def __getAllParticipants(self, context):
        return [{'who': (avatar.avatarName), 'nameTagColor': (avatar.nameTagColor), 'userId': (avatar.userId), 'hasVIPPass': (avatar.avatarInfo['hasVIPPass']), 'hasAccessPass': (avatar.avatarInfo['hasAccessPass'])} for avatar in self.__sessionWindow.avatars]

    @imvuCallHandlers.register
    def __showVipUpsell(self, context):
        self.__serviceProvider.dialogManager.showModal(context.parentWindow, imvu.dialog.WhisperVIPUpsellDialog())
        return

    @imvuCallHandlers.register
    def __notifyChatMessage(self, context, line, to):
        if self.__sessionWindow.isDisposed():
            return
        if not line.startswith('*'):
            if self.__sessionWindow.myAvatar:
                self.__sessionWindow.myAvatar.addBubble(line)
        self.__sessionWindow.notifyChatMessage(line, to=to)
        return

    @imvuCallHandlers.register
    def __cancelChatMessage(self, context, outgoingMessageId):
        if self.__sessionWindow.isDisposed():
            return
        self.__sessionWindow.cancelChatMessage(outgoingMessageId)
        return

    def __copyCb(self, context):
        selection = context.callFunction('(function(){return window.getSelection().toString()})')
        self.__platformService.setClipboardText(selection)
        return

    def __pasteCb(self, context):
        text = self.__platformService.getClipboardText()
        if text:
            context.callFunction('(function(x){IMVU.Client.ChatTool.pasteText(x)})', text)
        return

    @imvuCallHandlers.register
    def __showProductInfoDialog(self, context, product_id):
        self.__serviceProvider.eventBus.fire(self, 'ShowProductInfoDialog', {'pid': product_id})
        return

    @imvuCallHandlers.register
    def __tryOnProduct(self, context, productId):
        self.__sessionWindow.tryProduct(productId)
        self.__sessionWindow.getSession().sendImMessage('*imvu:try %s' % productId)
        return

    @imvuCallHandlers.register
    def __takeOffProduct(self, context, productId):
        self.__sessionWindow.getSession().sendImMessage('*remove %s' % productId)
        return

    @imvuCallHandlers.register
    def __showHistoryContextMenu(self, context, pageX, pageY):
        menuDesc = [imvu.menu.Item('Copy', (lambda : self.__copyCb(context)))]
        senderPos = context.getPos()
        pageX += senderPos.x
        pageY += senderPos.y
        self.__menuFactory.trackPopupMenu(menuDesc, context.parentWindow, (pageX, pageY))
        return

    @imvuCallHandlers.register
    def __showInputContextMenu(self, context, pageX, pageY):
        menuDesc = [imvu.menu.Item(self.__serviceProvider.translationTable.LS('Copy'), (lambda : self.__copyCb(context))),
         imvu.menu.Item(self.__serviceProvider.translationTable.LS('Paste'), (lambda : self.__pasteCb(context)))]
        senderPos = context.getPos()
        pageX += senderPos.x
        pageY += senderPos.y
        self.__menuFactory.trackPopupMenu(menuDesc, context.parentWindow, (pageX, pageY))
        return

    @imvuCallHandlers.register
    def __getChatId(self, context):
        return self.__sessionWindow.getSession().getChatId()

    # IMVU room antibot patch
    @imvuCallHandlers.register
    def __getAntibotWhitelist(self, context):
        import im.antibot
        return im.antibot.get_whitelist_display()

    @imvuCallHandlers.register
    def __getAntibotProtectionStatus(self, context):
        import im.antibot
        session = self.__sessionWindow.getSession()
        inner = getattr(session, 'innerSession', None)
        if inner is not None:
            session = inner
        return im.antibot._protection_status_info(session)

    @imvuCallHandlers.register
    def __addAntibotWhitelistUser(self, context, userId, avatarName=None):
        import im.antibot
        ok, whitelist = im.antibot.add_to_whitelist(userId, avatarName)
        self.__publishAntibotProtectionStatus(whitelist)
        return {'ok': ok, 'whitelist': whitelist}

    @imvuCallHandlers.register
    def __removeAntibotWhitelistUser(self, context, userId):
        import im.antibot
        ok, whitelist = im.antibot.remove_from_whitelist(userId)
        self.__publishAntibotProtectionStatus(whitelist)
        return {'ok': ok, 'whitelist': whitelist}

    def __publishAntibotProtectionStatus(self, whitelist=None):
        import im.antibot
        session = self.__sessionWindow.getSession()
        inner = getattr(session, 'innerSession', None)
        if inner is not None:
            session = inner
        info = im.antibot._protection_status_info(session)
        if whitelist is not None:
            info['whitelist'] = whitelist
        self.__serviceProvider.eventBus.fire(
            self.__sessionWindow,
            'SessionWindow.AntibotProtectionStatus',
            info,
        )
        return


class ChatLogGeckoListener(object):
    imvuCallHandlers = imvu.gecko.HandlerList()

    def __init__(self, serviceProvider, userAccount, sessionWindow, chatHistory, flagMessage=None):
        self.__serviceProvider = serviceProvider
        self.__userAccount = userAccount
        self.__sessionWindow = sessionWindow
        self.__chatHistory = chatHistory
        self.__flagMessage = flagMessage or LString("This room's chat history will be sent to Customer Service for review.")
        return

    @imvuCallHandlers.register
    def __showChatLogFlaggingDialog(self, context, avatar_id, message_index):
        session = self.__sessionWindow.getSession()
        chatLog = self.__chatHistory.get(stringify=False)
        if not chatLog:
            self.__serviceProvider.dialogManager.showModal(self.__sessionWindow.window, imvu.dialog.AlertDialog(self.__serviceProvider.translationTable.LS('Flagging Error'), self.__serviceProvider.translationTable.LS('There is no chat message to flag.')))
            return
        sessionAvatars = self.__sessionWindow.avatars
        avatarNameColorMap = {}
        for sessionAvatar in sessionAvatars:
            avatarNameColorMap[sessionAvatar.avatarName] = sessionAvatar.nameTagColor

        info = {'content': {'id': avatar_id, 
                       'chatLog': chatLog, 
                       'dialogSize': [
                                    540, 600], 
                       'avatarNameColorMap': avatarNameColorMap, 
                       'message_index': message_index, 
                       'chat_session_id': (session.getChatId())}, 
           'size': (540, 600), 
           'uri': 'chrome://imvu/content/dialogs/flag_content/index_chatlog.html', 
           'title': (LString('Flagging Chat')), 
           'message': (self.__flagMessage), 
           'service_url': '/api/flag_content/flag_chatlog.php'}
        self.__serviceProvider.dialogManager.showModal(self.__sessionWindow.window, imvu.dialog.ModalFlaggingDialog(self.__serviceProvider, self.__userAccount, info))
        return


class ChatTool(HtmlTool):
    toolName = 'chat'
    imvuCallHandlers = imvu.gecko.HandlerList()

    def __init__(self, serviceProvider, sessionWindow, parentWindow, userAccount, parentInputEventHandler, geckoListener=None, allowShopping=False, allowClose=False):
        self.__sessionWindow = sessionWindow
        self.__allowShopping = allowShopping
        self.__allowClose = allowClose
        serviceProvider.invoke(super(ChatTool, self).__init__, parentWindow=parentWindow, parentInputEventHandler=parentInputEventHandler, geckoListeners=[
         serviceProvider.create(ChatToolGeckoListener),
         serviceProvider.create(ChatLogGeckoListener, chatHistory=sessionWindow.chatHistory),
         IMQGeckoListener(serviceProvider),
         geckoListener,
         self], uri='chrome://imvu/content/tool/chat/index.html')
        self.bindKey((lambda : True), ord('C'), ctrl=True)
        self.bindKey((lambda : True), ord('V'), ctrl=True)
        return

    def show(self):
        super(ChatTool, self).show()
        self.__sessionWindow.setNumBubblesVisible(2)
        return

    def hide(self):
        super(ChatTool, self).hide()
        self.__sessionWindow.setNumBubblesVisible(-1)
        return

    def canLoseFocus(self):
        return False

    @imvuCallHandlers.register
    def __allowShopping(self, context):
        return self.__allowShopping

    @imvuCallHandlers.register
    def __allowClose(self, context):
        return self.__allowClose

    @imvuCallHandlers.register
    def __focusChat(self, window):
        window.onActivate()
        return

