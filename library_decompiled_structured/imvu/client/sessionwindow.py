# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.13.13 (tags/v3.13.13:01104ce, Apr  7 2026, 19:25:48) [MSC v.1944 64 bit (AMD64)]
# Embedded file name: imvu\client\sessionwindow.pyo
# Compiled at: 2026-05-27 16:08:57
import StringIO, base64, re, urlparse, xmlrpclib, urllib, imvu.client.scenewindow, imvu.fs, imvu.menu, imvu.network, imvu.scene.avatarmodel, imvu.scene.scenemodel, imvu.scene.roommodel, imvu.widget.widgetspace, im.meet, im.antibot
from imvu import inputevent
from imvu.translation import LString, FLString
from im.AvatarController import AvatarController
from im.AwayPresenter import AwayPresenter
from im.RoomController import RoomController
from im.commands import CommandManager
from imvu import avatarwindow
from imvu import product
from imvu.client.SessionWindowInputEventHandler import SessionWindowInputEventHandler
from imvu.client.chathistory import ChatHistory
from imvu.event import EventSink, EventBus
from imvu.flash import FlashCallHandler
from imvu.flash.FlashContext import FlashContext
from imvu.flash.FlashUrlLoader import FlashUrlLoader
from imvu.imq.MQManager import MQManager
from imvu.image import Image
from imvu.macro import MacroManager
from imvu.network import networkExceptions
from imvu.http import NetworkSchemaError
import imvu.opsys
from imvu.session import ChangeableSession
from imvu.task import CallPeriodically, TaskOwner, attachedtask, NamedTaskCollection, task, Sleep, Return, Event, WaitForNextFrame, ActiveObject, activemethod
from imvu.util import assertInRelease, WeakInterfaceBridge, instance_counter, getStringEncoding, NoMonkeyPatching, GenericObject
from imvu.util.thread import assertOnMainThread
from imvu.LoginCollisionException import LoginCollisionException
from imvu.scene.scenepresenter import ScenePresenter
import logging, HTMLParser
logger = logging.getLogger('imvu.' + __name__)
WHITE_ROOM_PRODUCT_ID = 10968
PROGRESS_VAL_INTERVAL = 0.05
CouldNotGetRoomStateMessage = (
 LString('A temporary error has prevented this room from loading. Please try again.'), 900)
CannotChangeRoomsInPublicRoomChatMessage = (LString("You can't change rooms while in a chat."), 90)
CannotTryOnRoomProductMessage = (LString("Sorry, you currently can't try on a room product"), 200)
CannotAddFurnitureToLockedRoomMessage = (LString("You can't add furniture to a Locked Room."), 90)
ItemCannotBeWornWithAvatarMessage = (LString('Sorry, this item cannot be worn with your avatar.'), 300)
ItemIsBundleMessage = (LString('This item is not a 3d product. (It may be a bundle)'), 300)
HeadNodeName = u'Head'
RoomSizeName = u'RoomSize'

class FafManager(TaskOwner):

    def __init__(self, fafProvider, serviceProvider):
        TaskOwner.__init__(self, serviceProvider.taskScheduler)
        self.__fafProvider = fafProvider
        self.__timeProvider = serviceProvider.timeProvider
        self.__fafMessages = {}
        return

    def __fafMessageCb(self, *args, **kwargs):
        return

    def setFafMessageInfo(self, msg_name, msg_info):
        msg_info['end_time'] = self.__timeProvider() + msg_info['duration']
        cur_info = self.__fafMessages.get(msg_name, {})
        if 'fafMessageId' in cur_info:
            msg_info['fafMessageId'] = cur_info['fafMessageId']
            self.__fafProvider.messageReplaceText(cur_info['fafMessageId'], msg_info['dialogText'])
        else:
            msg_info['fafMessageId'] = self.__fafProvider.messageShow(msg_info['dialogText'], 9000)

            @task
            def closeWhenDone():
                while True:
                    info = self.__fafMessages[msg_name]
                    now = self.__timeProvider()
                    if now >= info['end_time']:
                        break
                    else:
                        yield Sleep(info['end_time'] - now)
                    info = self.__fafMessages[msg_name]

                self.__fafProvider.messageClose(info['fafMessageId'])
                self.__fafMessages.pop(msg_name)
                return

            self.attachTask(closeWhenDone())
        if 'updateHeight' in msg_info:
            self.__fafProvider.messageUpdateHeight(msg_info['fafMessageId'], msg_info['updateHeight'])
        self.__fafMessages[msg_name] = msg_info
        return


def findUnoccupiedSeatNumber(avatars, userId):
    minSeat = 1
    maxSeat = 0
    occupiedSeats = []
    for pyAv in avatars:
        seatNumber, furniInstanceId = pyAv.avatarModel.seat
        if furniInstanceId == 0:
            occupiedSeats.append(seatNumber)
            maxSeat = max(maxSeat, seatNumber)

    if minSeat > maxSeat:
        return minSeat
    i = minSeat
    while i <= maxSeat and i in occupiedSeats:
        i += 1

    return i


SELF_AVATAR_COLOR = (255, 255, 255)
OTHER_AVATAR_COLORS = (
 (125, 210, 213),
 (200, 172, 233),
 (248, 205, 70),
 (131, 214, 150),
 (246, 170, 132),
 (138, 193, 239),
 (174, 209, 85),
 (226, 168, 219),
 (181, 188, 235))

class SessionWindow(ActiveObject, EventSink, NoMonkeyPatching):
    __metaclass__ = instance_counter.RegisteredInstanceCounter
    __commandHandlers = {}

    def __commandHandler(command, _SessionWindow__commandHandlers=__commandHandlers):

        def dec(handler):
            __commandHandlers[command] = handler
            return handler

        return dec

    __messageHandlers = []
    __messageHandler = __messageHandlers.append

    def __init__(self, imSession, productLoader, userAccount, modeManager, serviceProvider, actionList, htmlOverlayFactory, productAuthorizer, chatMode='Private', forcedRoom=None, forcedRoomState=None, initialAvatarDefinition=None, useProductPolicy=None, editedProductId=None, parentInputEventHandler=None, sceneWindow=None):
        self.__serviceProvider = serviceProvider.nestedProvider(sessionWindow=self)
        del serviceProvider
        assertInRelease(userAccount)
        assertOnMainThread()
        self.__actionList = actionList
        self.__chatMode = chatMode
        self.__myAvatarDownloadSize = None
        logger.info('ImSessionWindow(): %r', imSession)
        startTime = self.__serviceProvider.timeProvider()
        ActiveObject.__init__(self, self.__serviceProvider.taskScheduler)
        EventSink.__init__(self, self.__serviceProvider.eventBus)
        self.__disposed = False
        self.__userAccount = userAccount
        self.__useProductPolicy = useProductPolicy
        self.__parentInputEventHandler = parentInputEventHandler
        self.__productAuthorizer = productAuthorizer
        self.__currentRoomOwnerInfo = {}
        self.__seatAssignmentTasks = NamedTaskCollection(self.__serviceProvider.taskScheduler)
        self.__animationTasks = NamedTaskCollection(self.__serviceProvider.taskScheduler)
        self.__chatHistory = ChatHistory()
        self.__photoWidget = None
        self.__notSavingPhoto = Event()
        self.__notSavingPhoto.set()
        self.__outfitInfoForPictureChange = {}
        self.__privateChatOwnerLeft = Event()
        self.__secondsUntilPrivateChatCloses = 120
        self.__commandManager = CommandManager()
        self.canModifyDefaultOutfit = False
        self.__session = ChangeableSession(self.__serviceProvider, self.__commandManager, imSession)
        for eventName, eventListener in self.__sessionEventListeners:
            self.registerEventListener(self.__session, eventName, eventListener)

        self.__session.setCommandManager(self.__commandManager)
        self.__serviceProvider.register(session=self.__session)
        self.__htmlOverlayFactory = htmlOverlayFactory
        self.__widgetSpace = imvu.widget.widgetspace.WidgetSpace(self.__serviceProvider, self.__userAccount, self.__addFlashOverlay, self.__commandManager)
        self.__flashRenderContexts = []
        self.__productLoader = productLoader
        self.__modeManager = modeManager
        self.__fafManager_ = FafManager(self, self.__serviceProvider)
        self.attachTaskOwner(self.__fafManager_)
        self.macroManager = MacroManager(self.__serviceProvider)
        self.__forcedRoom = forcedRoom
        self.__forcedRoomState = forcedRoomState
        self.__roomStateIsLocal = self.__forcedRoom is not None or self.__forcedRoomState is not None
        self.__nonAPPUsers = []
        self.__nonAPUsers = []
        self.__errorRoomPid = 0
        self.configIdleEvent = Event()
        self.configIdleEvent.set()
        assertOnMainThread()
        assertInRelease(self.__pilotUserId)
        self.__showNameLabels = True
        self.__modeShowAvatarLabels = False
        self.__showingAvatarNameLabels = False
        logger.info('SessionWindow.__createWindow')
        self.__sceneWindow = sceneWindow
        self.__userAccount.recordFact('Open 3D Window', {'graphicsRenderer': (self.__serviceProvider.prefService.getPref('graphicsRenderer'))})
        self.registerEventListener(self.__sceneWindow.avatarWindow, 'GiftArrived', self.__handleGiftArrived)
        self.registerEventListener(self.__serviceProvider.prefService, 'PrefChanged-avatarLabelDisplay', self.__avatarLabelDisplayChange)
        self.__initScene(initialAvatarDefinition, useProductPolicy, editedProductId)
        FlashUrlLoader.register(serviceProvider=self.__serviceProvider)
        FlashUrlLoader.registerUrlHandler(self.__handleFlashUrlRequest)
        self.__inputEventHandler = self.__serviceProvider.create(SessionWindowInputEventHandler, modeManager=modeManager)
        for command, handler in self.__commandHandlers.items():
            self.__commandManager.registerCommandHandler(command, handler.__get__(self, type(self)))

        for messageHandler in self.__messageHandlers:
            self.__commandManager.registerMessageHandler(messageHandler.__get__(self, type(self)))

        self.__commandManager.registerMessageDeliveredHandler(self.__handleMessageDeliveryNotification)
        self.changeImSession(newImSession=imSession)
        self.__awayPresenter = AwayPresenter(self.__serviceProvider, fafProvider=self)

        def periodicallyCallMethod(method, interval, immediatelyCall=True):
            self.attachTask(CallPeriodically(method, interval, immediatelyCall=immediatelyCall))
            return

        periodicallyCallMethod(self.__considerSendingServerNotify, 60, False)
        periodicallyCallMethod(self.__logAvatarAndRoomState, 120)
        periodicallyCallMethod(self.__logAvatarSize, 30)
        periodicallyCallMethod(self.__stepLoadingProductsMessage, 1)
        logger.info('ImSessionWindow(): done %.2f', self.__serviceProvider.timeProvider() - startTime)
        self.__showAvatarNameLabels(False)
        self.__lastOutfit = []
        self.attachTask(self._handlePrivateChatOwnerAbsent())
        return

    def getModeManager(self):
        return self.__modeManager

    @property
    def commandManager(self):
        return self.__commandManager

    def addHtmlOverlay(self, overlay):
        self.attachTaskOwner(overlay)
        return

    @property
    def sceneViewer(self):
        if not self.__sceneWindow:
            return None
        else:
            return self.__sceneWindow.avatarWindow

    @task
    def updateLoadingProductsDisplay(self):
        yield WaitForNextFrame()

        def getRoomStateLoadProgressFn():

            @task
            def getRoomStateLoadProgress():
                if self.__roomController is None:
                    yield Return(0)
                if not self.__roomController.roomState:
                    yield Return(0.5)
                else:
                    yield Return(1)
                return

            result = GenericObject()
            result.getProgress = getRoomStateLoadProgress
            result.text = self.__serviceProvider.translationTable.LS('Downloading blueprint...')
            return result

        def getFurniProgressFn():

            @task
            def getLowResTextureConfigProgress():
                if self.__roomController is None:
                    yield Return(0)
                contents = yield self.__roomController.roomState.getRoomContents()
                if len(contents) == 0:
                    yield Return(1)
                yield Return(float(self.__scenePresenter.getConfiguredFurnitureCount() + len(self.__roomController.slotsFailedAuth)) / len(contents))
                return

            result = GenericObject()
            result.getProgress = getLowResTextureConfigProgress
            result.text = self.__serviceProvider.translationTable.LS('Arranging furniture...')
            return result

        self.__serviceProvider.eventBus.fire(self, 'LoadingProgress', dict(progress=0, text=self.__serviceProvider.translationTable.LS('Building room...')))
        for providerFn in [getRoomStateLoadProgressFn, getFurniProgressFn]:
            progressProvider = providerFn()
            while True:
                yield Sleep(0.1)
                real_progress = yield progressProvider.getProgress()
                self.__serviceProvider.eventBus.fire(self, 'LoadingProgress', dict(progress=real_progress, text=progressProvider.text))
                if real_progress == 1.0:
                    break

        return

    def getAvatarWindowSize(self):
        if self.__sceneWindow:
            return self.__sceneWindow.avatarWindow.getRenderedWindow().getClientSize()
        else:
            return (0, 0)

        return

    def __initScene(self, initialAvatarDefinition, useProductPolicy, editedProductId):
        self.__avatarControllers = []
        self.avatarProductLoadingHalter = None
        self.__sceneWindow.avatarWindow.setAvatarWindowUser(WeakInterfaceBridge(avatarwindow.PiAvatarWindowUser, self))
        self.__sceneModel = imvu.scene.scenemodel.SceneModel(self.__serviceProvider.eventBus)
        self.__sceneModel.setPilotUserId(self.__pilotUserId)
        roomModel = imvu.scene.roommodel.RoomModel(self.__serviceProvider.eventBus)
        self.__sceneModel.setRoomModel(roomModel)
        self.__roomController = self.__serviceProvider.create(RoomController, roomModel=roomModel, parentWindow=self.window, productLoader=self.__productLoader, roomOwners=self.__session.getRoomOwners(), isAlwaysDriver=self.__session.isAlwaysDriver())
        self.__scenePresenter = ScenePresenter(self.__serviceProvider, self.__session, self.__sceneWindow.avatarWindow, self.__sceneModel, self.__roomController, soundCutoffCallback=self.__userAccount.shouldEnforceSoundLimit, productLoader=self.__productLoader)
        self.registerEventListener(self.__roomController, 'RoomStateChanged', self.__roomStateChanged)
        if self.__session.shouldResetRoomDefinitionAtStartup():
            self.__resetRoomFromDefinition()
        if not initialAvatarDefinition:
            initialAvatarDefinition = self.__userAccount.defaultOutfit
        self.__avatarColorIndex = 0
        self.addNewAvatar(self.__userAccount.getUserInfo(), definition=initialAvatarDefinition, useProductPolicy=useProductPolicy, editedProductId=editedProductId)
        self.registerEventListener(self.__serviceProvider.mqManager, MQManager.IMQ_CONNECTED_EVENT, self.__imqConnected)
        return

    def showNameLabels(self, show):
        self.__showNameLabels = show
        self.__showAvatarNameLabels(self.__modeShowAvatarLabels)
        return

    def modeShowsAvatarLabels(self, show=True):
        self.__modeShowAvatarLabels = show
        self.__showAvatarNameLabels(self.__modeShowAvatarLabels)
        return

    @property
    def showingAvatarNameLabels(self):
        return self.__showingAvatarNameLabels

    def __showAvatarNameLabels(self, show):
        self.__showingAvatarNameLabels = self.__serviceProvider.prefService.getPref('avatarLabelDisplay') != 'Bottom' and self.__modeShowAvatarLabels and show and self.__showNameLabels
        for av in self.__avatarControllers:
            av.showNameLabel(self.__showingAvatarNameLabels, htmlOverlayFactory=self.__htmlOverlayFactory)

        self.__sceneWindow.avatarWindow.drawNameLabelBar(self.__showNameLabels and not self.__showingAvatarNameLabels)
        return

    def __avatarLabelDisplayChange(self, event):
        self.__showAvatarNameLabels(True)
        return

    @property
    def sceneModel(self):
        return self.__sceneModel

    @property
    def sceneWindow(self):
        return self.__sceneWindow

    @property
    def window(self):
        if self.__sceneWindow:
            return self.__sceneWindow.renderedWindow
        else:
            return
            return

    @task
    def allowsAccessPassPlus(self):
        if self.__session.isPrivate() and self.__session.isRoomSession():
            yield Return(self.__nonAPPUsers == [])
        if not self.__session.isPrivate() and self.__session.isRoomSession() and self.__roomController.roomInstanceId:
            roomInfo = yield self.__serviceProvider.clientGateway.getRoomCardInfo(self.__roomController.roomInstanceId)
            if not roomInfo.get('allowApPlusProducts', False) and not roomInfo.get('isAPPlus', False):
                yield Return(False)
            else:
                yield Return(True)
        else:
            yield Return(True)
        return

    @task
    def allowsAccessPass(self):
        if not self.__userAccount.inSeparateGAAPRollout():
            yield Return(True)
        if self.__session.isPrivate() and self.__session.isRoomSession():
            yield Return(self.__nonAPUsers == [])
        if not self.__session.isPrivate() and self.__session.isRoomSession() and self.__roomController.roomInstanceId:
            roomInfo = yield self.__serviceProvider.clientGateway.getRoomCardInfo(self.__roomController.roomInstanceId)
            if not roomInfo.get('allowApProducts', False) and not roomInfo.get('isAP', False):
                yield Return(False)
            else:
                yield Return(True)
        else:
            yield Return(True)
        return

    @task
    def __addFurnitureToRoom(self, pyAv, product):
        if self.__session.isRoomSession():
            try:
                roomInfo = yield self.__serviceProvider.clientGateway.getRoomCardInfo(self.__roomController.roomInstanceId)
                products = yield self.__serviceProvider.productInfoManager.getProductsByIds([product.getProductId()])
                if not roomInfo.get('allowApProducts', False):
                    for prodInfo in products:
                        if not roomInfo['isAP'] and prodInfo['products_mature'] == 'Y' and pyAv.userId == self.__userAccount.getUserId():
                            self.__serviceProvider.dialogManager.showModal(self.window, imvu.dialog.AlertDialog(self.__serviceProvider.translationTable.LS("Can't Add Product to Room"), self.__serviceProvider.translationTable.LS('Sorry, you cannot place an AP-rated item in your GA room. Please make the room AP only or choose another item to decorate your room. Thank you.')))
                            return

                if not roomInfo.get('allowApPlusProducts', False):
                    for prodInfo in products:
                        if not roomInfo.get('isAPPlus', False) and prodInfo['products_mature'] == '4' and pyAv.userId == self.__userAccount.getUserId():
                            self.__serviceProvider.dialogManager.showModal(self.window, imvu.dialog.AlertDialog(self.__serviceProvider.translationTable.LS("Can't Add Product to Room"), self.__serviceProvider.translationTable.LS('Sorry, you cannot place an AP Plus-rated item in your non-AP Plus room. Please make the room AP Plus only or choose another item to decorate your room. Thank you.')))
                            return

            except networkExceptions:
                logger.exception("couldn't get info for room instance id %r", self.__roomController.roomInstanceId)
                return

        if not self.__canUseFurnitureProduct(pyAv):
            return
        if not self.__checkUseProductPolicy(product, self.__roomController):
            return
        with self.__roomController.undoActivated():
            self.__roomController.useProduct(product)
        return

    def __unhandledAvatarProduct(self, pyAv, product, isWrongBodyType=False):
        if self.isDisposed():
            return
        logger.info('__unhandledAvatarProduct(): %r %r %r', pyAv, product.getProductId(), isWrongBodyType)
        if product.isUiSkin():
            return
        if product.isFurniture():
            if pyAv.userId != self.__pilotUserId:
                return
            self.attachTask(self.__addFurnitureToRoom(pyAv, product))
        elif product.isEnvironment():
            if self.__session.isRoomSession():
                if self.__session.allowRoomShellOverwrite() and self.__session.isOwner(pyAv.userId):
                    self.__fireRoomShellChangedFact(roomOwner=pyAv.userId, roomPid=product.getProductId(), numParticipants=len(self.__session.getParticipantUserIds()))
                    self.__resetPublicRoomFromDefinition(roomOwner=pyAv.userId)
                    return
                if self.isRoomOwner(pyAv.userId) and self.__roomController.roomPid == product.getProductId():
                    return
                if self.__session.allowLoadNewRoom():
                    self.attachTask(self.__loadRoom(pi=product, roomOwner=pyAv.userId))
                if pyAv.userId == self.__pilotUserId and self.__roomController.roomPid != product.getProductId():
                    if self.__session.allowLoadNewRoom():
                        self.attachTask(self.__loadRoom(pi=product, roomOwner=pyAv.userId))
                    else:
                        self.messageShow(*CannotChangeRoomsInPublicRoomChatMessage)
            elif self.__session.isLocalChat():
                if self.isRoomOwner(pyAv.userId) and self.__roomController.roomPid != product.getProductId():
                    self.__fireRoomShellChangedFact(roomOwner=pyAv.userId, roomPid=product.getProductId(), numParticipants=len(self.__session.getParticipantUserIds()))
                    if pyAv.userId == self.__pilotUserId:
                        changeroom_msg = '*imvu:changeRoom %r' % product.getProductId()
                        self.__session.sendImMessage(changeroom_msg)
                    self.attachTask(self.__loadRoom(pi=product, roomOwner=pyAv.userId))
            else:
                if self.isRoomOwner(pyAv.userId) and self.__roomController.roomPid == product.getProductId():
                    return
                else:
                    if not self.__checkUseProductPolicy(product, self.__roomController):
                        return
                    if pyAv.userId == self.__pilotUserId and not self.isRoomOwner(pyAv.userId):
                        self.__fireRoomShellChangedFact(roomOwner=pyAv.userId, roomPid=product.getProductId(), numParticipants=len(self.__session.getParticipantUserIds()))
                        changeroom_msg = '*imvu:changeRoom %r' % product.getProductId()
                        logger.info('taking control of room, changeroom_msg: %r session: %s', changeroom_msg, self.__session)
                        self.__session.sendImMessage(changeroom_msg)
                    self.__session.setLocation(product.getProductId())
                    self.attachTask(self.__loadRoom(pi=product, roomOwner=pyAv.userId))
                    return

        else:
            self.maybeShowUnusableProductMessage(pyAv.userId, product.getProductId(), isWrongBodyType)
            return
        return

    def __fireRoomShellChangedFact(self, roomOwner, roomPid, numParticipants):
        self.__userAccount.recordFact('chat_room_shell_change', dict(room_pid=roomPid, changer_cid=roomOwner, num_participants=numParticipants))
        return

    def onBadProduct(self, event):
        self.maybeShowUnusableProductMessage(event.info['userId'], event.info['pid'], False)
        return

    def showUnusableProductMessage(self, event):
        if event.info['isBundleProduct']:
            self.messageShow(*ItemIsBundleMessage)
        else:
            self.messageShow(*ItemCannotBeWornWithAvatarMessage)
        return

    def maybeShowUnusableProductMessage(self, userId, pid, isWrongGender=False, isBundleProduct=False):
        if userId == self.__pilotUserId:
            if isBundleProduct:
                self.__serviceProvider.eventBus.fire(self, 'productUseFailed', dict(message='This item is not a 3d product. (It may be a bundle with the product you actually want inside of it)', pid=str(pid), isWrongGender=isWrongGender, isBundleProduct=isBundleProduct))
            else:
                self.__serviceProvider.eventBus.fire(self, 'productUseFailed', dict(message='This item cannot be worn by your avatar.', pid=str(pid), isWrongGender=isWrongGender, isBundleProduct=isBundleProduct))
        return

    def tryProduct(self, productId):
        self.__usePidsOnAvatar(pyAv=self.myAvatar, pids=[productId], trialAuth=True)
        return

    def __parsePidsStr(self, pids_str):
        pids = []
        for pid in pids_str.split():
            try:
                pids.append(int(pid))
            except ValueError:
                logger.exception('not an integer: %r', pid)

        return pids

    def __usePidsStrOnAvatar(self, pyAv, pids_str):
        pids = self.__parsePidsStr(pids_str)
        self.__usePidsOnAvatar(pyAv, pids)
        return

    def __shouldLeaveOutfitPhotoMode(self, pyAv, pi):
        if self.isDisposed():
            return False
        else:
            if pi is None or not pi.isClothingProduct():
                return False
            if pyAv != self.myAvatar:
                return False
            if not self.__outfitInfoForPictureChange:
                return False
            if pi.getProductId() in self.__getCurrentPidsFromOutfitInfo(self.__outfitInfoForPictureChange):
                return False
            return True

    def __usePidsOnAvatar(self, pyAv, pids, trialAuth=False, initialOutfit=False):
        logger.info('__usePidsOnAvatar(): pids: %r pyAv: %r, session: %s', pids, pyAv, self)
        if self.__roomController.roomPid in pids:
            pids.remove(self.__roomController.roomPid)
            if not pids:
                return

        def ulp(av, pid, pi, exn):
            if self.__shouldLeaveOutfitPhotoMode(pyAv, pi):
                self.__cancelOutfitPhoto()
            if exn:
                try:
                    self.maybeShowUnusableProductMessage(pyAv.userId, pid, False, 'No CFL' == str(exn))
                except UnicodeEncodeError:
                    self.maybeShowUnusableProductMessage(pyAv.userId, pid, False, False)

                return
            if not self.__checkUseProductPolicy(pi, pyAv):
                return
            try:
                av.applyProduct(pi)
            except imvu.scene.SceneStateException as e:
                if self.__shouldOpenRoomInNewChat(av, pi, trialAuth):
                    if av.userId != self.__userAccount.getUserId():
                        return
                    self.attachTask(self.openRoom(pid))
                else:
                    self.__unhandledAvatarProduct(av, pi, isinstance(e, imvu.scene.IncompatibleBodyException))

            return

        pyAv.usePids(pids, useLoadedProduct=ulp, trialAuth=trialAuth)
        if initialOutfit or pyAv.userId != self.__pilotUserId:
            pyAv.clearUndoList()
        return

    def __shouldOpenRoomInNewChat(self, av, pi, trialAuth):
        if not pi.isEnvironment():
            return False
        if trialAuth:
            return False
        if self.__session.allowLoadNewRoom():
            return False
        if self.__session.isPrivate() and self.__session.isRoomSession() and not self.__session.allowRoomShellOverwrite():
            return True
        return False

    @task
    def __applyThenRemoveProduct(self, pyAv, pid, seconds):
        logger.info('__applyThenRemoveProduct(): pid: %r time: %r pyAv: %r', pid, seconds, pyAv)
        pi = yield self.__productLoader.createProductInstance(pyAv.userId, pid)
        self.__usePidsOnAvatar(pyAv, [pid])
        yield Sleep(seconds)
        try:
            yield self.removeProductById(pid, pyAv)
        except Exception:
            pass

        return

    def __handleGiftArrived(self, event):
        receiver = int(event.info['receiver'])
        pyAv = self.pyAvForUserId(userId=receiver)
        assertInRelease(pyAv)
        delay = self.__userAccount.get3dGiftingConfig().get('productDuration', 30)
        pids = self.__userAccount.get3dGiftingConfig().get('pids', [])
        for pid in pids:
            self.attachTask(self.__applyThenRemoveProduct(pyAv, pid, delay))

        return

    def isRoomOwner(self, userId=None):
        if userId is None:
            userId = self.__pilotUserId
        if self.__session.isLocalChat():
            return self.__session.isOwner(userId)
        else:
            if not self.__currentRoomOwnerInfo.get('userId', 0):
                return True
            if self.__session.isRoomSession():
                return self.__session.isOwner(userId)
            roomOwnerUserId = self.__currentRoomOwnerInfo.get('userId', 0)
            return roomOwnerUserId == userId

    def getAvatarnames(self):
        names = []
        for pyAv in self.__avatarControllers:
            if pyAv.userId != self.__pilotUserId:
                names.append(pyAv.avatarName)

        return names

    def getSession(self):
        return self.__session

    @__commandHandler('*imvu:isPureUser')
    def __isPureUserImpl(self, command, params, messageObject):
        self.__session.sawPureUser(self.__userAccount)
        return

    @__commandHandler('*boot')
    def __bootImpl(self, command, params, messageObject):
        logger.info('Received *boot message: %r', messageObject)
        if self.__session and self.__session.isRoomSession():
            try:
                _, bootee = map(int, params.split())
            except (ValueError, AttributeError):
                logger.exception('invalid arguments to boot command')
                return

            booter = self.pyAvFromMessage(messageObject).userId
            if self.__session.canBoot(booter, bootee):
                if self.__pilotUserId == bootee:
                    logger.info('user %r is being booted', bootee)
                    self.__serviceProvider.eventBus.fire(self, 'SessionWindow.BootedFromChat', {'roomInstanceId': (self.__session.getRoomInstanceId())})
                    self.__userAccount.recordFact('room_boot_user', dict(booterCid=booter, roomInstanceId=self.__session.getRoomInstanceId(), timestamp=self.__serviceProvider.timeProvider()))
                elif self.__pilotUserId == booter:
                    logger.info('owner received boot message')
                    self.__session.bootUser(bootee)

                @task
                def showStateMessage():
                    name = yield self.__serviceProvider.avatarInfoManager.getAvatarName(bootee)
                    self.messageShow(self.__serviceProvider.translationTable.FLS('{name} has been booted', name=name), 300)
                    return

                self.attachTask(showStateMessage())
        return

    @__commandHandler('*imvu:showGift')
    def __showGiftImpl(self, command, params, messageObject):
        logger.info('action_showGiftImpl(): command: %r params: %r message: %r', command, params, messageObject)
        if not self.__userAccount.shouldShow3dGifting():
            logger.info('3d gifting disabled, ignore')
            return
        else:
            if messageObject.fromId_ != 0:
                logger.info('message not from 0, ignore')
                return
            paramsList = params.split(' ', 4)
            try:
                senderId = int(paramsList[0])
                receiverId = int(paramsList[1])
                giftType = paramsList[2]
                giftId = int(paramsList[3])
                b1 = params.index('{')
                b2 = params.rindex('}')
                fafText = params[b1 + 1:b2]
            except Exception:
                logger.exception('could not parse gift info out of *imvu:showGift')
                return

            logger.info('action_showGiftImpl(): fafText: %r', fafText)
            senderAv = self.pyAvForUserId(senderId)
            receiverAv = self.pyAvForUserId(receiverId)
            if senderAv is None or receiverAv is None:
                logger.warning('No matching avatars in scene for gift')
                return
            travelFrames = self.__userAccount.get3dGiftingConfig().get('travelFrames', 30)
            bounceHeight = self.__userAccount.get3dGiftingConfig().get('bounceHeight', 5)
            bounceWidth = self.__userAccount.get3dGiftingConfig().get('bounceWidth', 10)
            senderAv.trigger3dGift(receiverAv, travelFrames, bounceHeight, bounceWidth)
            self.__sceneWindow.avatarWindow.newFireAndForgetMessage(fafText, 600)
            if self.__pilotUserId == receiverId:
                self.__userAccount.getInventoryState().refresh()
            if giftType == 'product':
                self.attachTask(self.displayShoppingEvent(byAvatar=senderAv, productId=giftId, eventName='SessionWindow.GiftProduct', toAvatar=receiverAv))
            return

    def __isRoomOwnerUnknown(self):
        return self.isRoomOwner(-1)

    @__commandHandler('*imvu:setRoomState')
    def __setRoomStateImpl(self, command, params, messageObject):
        userId = messageObject.getMessageFromId()
        if userId:
            assertInRelease(any(pyAv.userId_ == userId for pyAv in self.__avatarControllers))
        if self.__isRoomOwnerUnknown():
            self.__setRoomOwner(messageObject)
        if userId and not self.isRoomOwner(userId) and self.__session.isRoomSession():
            logger.info('ignoring setRoomState because session_window pilot != userId %r', userId)
            return
        self.__roomController.bringRoomStateCurrent(params)
        return

    @attachedtask
    def __controlMessageListener(self, event):
        command = event.info.get('command')
        if command == 'PlayAction':
            yield self.__playAction(event.info.get('actionInfo'))
        elif command == 'PlayCoopAction':
            self.__playTwoPartyAction(event.info.get('actionInfo'))
        return

    @task
    def __playAction(self, actionInfo):
        try:
            if actionInfo.get('furniSlotId'):
                self.__scenePresenter.playActionOnFurniture(int(actionInfo['furniSlotId']), actionInfo['actionName'])
            else:
                yield self.__loadAndTriggerAvatarActions(actionInfo.get('actionName', ''), 'product://%d/index.xml' % int(actionInfo['productId']), int(actionInfo['userId']), '', '', 0)
        except (KeyError, AttributeError):
            logger.exception('incomplete action info for __playAction: %r' % actionInfo)

        return

    def __playTwoPartyAction(self, actionInfo):
        try:
            pyAv = self.pyAvForUserId(int(actionInfo['userId']))
            slotId = int(actionInfo['furniSlotId'])
            furniSo = self.__scenePresenter.getFurnitureSceneObject(slotId)
            furniMd = self.__scenePresenter.getFurnitureModelDefinition(slotId)
            if pyAv and furniSo and furniMd:
                pyAv.triggerActionWithFurni(furniSo, furniMd, actionInfo['avatarActionPid'], actionInfo['avatarActionName'], actionInfo['furniActionPid'], actionInfo['furniActionName'])
            else:
                logger.exception('Scene objects not found in scene for user %r or slot %r (%r, %r, %r)', actionInfo['userId'], actionInfo['furniSlotId'], pyAv, furniSo, furniMd)
        except (KeyError, AttributeError):
            logger.exception('incomplete action info for __playTwoPartyAction: %r' % actionInfo)

        return

    @__commandHandler('*imvu:changeRoom')
    def __changeRoomImpl(self, command, params, messageObject):
        if messageObject.getMessageTimestamp() > self.__currentRoomOwnerInfo.get('timestamp', -1):
            self.__setRoomOwner(messageObject)
        else:
            logger.info('ignoring old changeRoom message %r %r', messageObject, self.__currentRoomOwnerInfo)
        return

    @task
    def openRoom(self, productId):
        result = None
        try:
            result = yield self.__userAccount.getOrMakeRoom(productId)
            newRoomInstanceId = result['room_state']['room_info']['room_instance_id']
        except (TypeError, KeyError, networkExceptions) as e:
            logger.exception('getOrMakeRoom result not valid: %r, exception type: %r, exception: %r', result, type(e), e)
            return

        session = self.getSession()
        if not newRoomInstanceId:
            return
        else:
            chatId = session.getChatId()
            if not chatId or not newRoomInstanceId:
                logger.info('openRoom in bad state: chatId: %r, newRoomInstanceId: %r', chatId, newRoomInstanceId)
                return
            try:
                result = yield self.__serviceProvider.chatGateway.setChatRoomInstanceId({'chatId': chatId, 
                   'roomInstanceId': newRoomInstanceId})
            except xmlrpclib.Fault as f:
                if f.faultCode == imvu.gateway.ERROR_ROOM_IN_USE:
                    try:
                        chat = yield self.__serviceProvider.chatGateway.getChatIdForRoomInstance({'roomInstanceId': newRoomInstanceId})
                    except networkExceptions:
                        logger.exception('chatGateway.getChatIdForRoomInstance(%r) failed', newRoomInstanceId)
                        return

                    if chat.get('chatId'):
                        yield self.__modeManager.joinPublicRoom(newRoomInstanceId)
                    return
                return
            except networkExceptions:
                logger.exception('chatGateway.setChatRoomInstanceId(%r, %r) failed', newRoomInstanceId, chatId)
                return

            if isinstance(result, dict) and result.get('success'):
                self.getSession().sendImMessage(messageText='*imvu:goto %s' % (newRoomInstanceId,))
            else:
                return
            return

    @__commandHandler('*imvu:goto')
    @attachedtask
    def __gotoImpl(self, command, params, messageObject):
        if not messageObject.getMessageFromId():
            logger.info('Unable to get userId for goto message.')
            return
        chatId = self.getSession().getChatId()
        try:
            roomInstanceIdResult = yield self.__serviceProvider.chatGateway.getChatRoomInstanceId({'chatId': chatId})
        except networkExceptions:
            logger.exception("couldn't get room instance ID for chat ID %r", chatId)
            return

        if not isinstance(roomInstanceIdResult, dict) or 'roomInstanceId' not in roomInstanceIdResult:
            logger.exception('room instance ID result was bogus')
            return
        roomInstanceId = roomInstanceIdResult['roomInstanceId']
        try:
            roomInfo = yield self.__serviceProvider.clientGateway.getRoomCardInfo(roomInstanceId)
        except networkExceptions:
            logger.exception("couldn't get info for room instance id %r", params)
            return

        pyAv = self.pyAvFromMessage(messageObject)
        oldRoomInstanceId = self.__session.getRoomInstanceId()
        info = {'gender': (pyAv.avatarInfo.gender), 
           'hasVIP': (pyAv.avatarInfo.isVIP), 
           'nameTagColor': (pyAv.nameTagColor), 
           'roomInfo': roomInfo, 
           'roomInstanceId': roomInstanceId, 
           'oldId': ('publicRoom%s' % oldRoomInstanceId), 
           'newId': ('publicRoom%s' % roomInstanceId), 
           'roomName': (HTMLParser.HTMLParser().unescape(roomInfo['name'])), 
           'title': (HTMLParser.HTMLParser().unescape(roomInfo['name'])), 
           'to': (messageObject.toId), 
           'userId': (pyAv.userId), 
           'who': (pyAv.avatarName)}
        if roomInfo['isAP'] and not self.__userAccount.hasAccessPass():
            return
        if roomInfo['isVIP'] and not self.__userAccount.hasVIPPass():
            return
        if self.__session.getRoomInstanceId() == params:
            return
        self.__session.setRoomInstanceId(params)
        self.__session.setAutoBootWhenOwnerLeaves(roomInfo.get('autoBootWhenOwnerLeaves', False))
        self.__session.setRoomOwners(roomInfo.get('roomOwners', []) or [])
        self._stopPrivateChatClosureTimeout()
        self.__resetPublicRoomFromDefinition(roomOwner=pyAv.userId)
        self.__serviceProvider.eventBus.fire(self, 'SessionWindow.ReplaceRoom', info)
        return

    def __setRoomOwner(self, messageObject):
        curId = self.__currentRoomOwnerInfo.get('userId', None)
        if not curId or messageObject.getMessageFromId() != curId:
            logger.info('new session pilot for user %r: %r', self.__pilotUserId, messageObject.getMessageFromId())
        self.__currentRoomOwnerInfo['userId'] = messageObject.getMessageFromId()
        self.__roomController.ownerId = messageObject.getMessageFromId()
        self.__serviceProvider.eventBus.fire(self, 'SessionWindow.setRoomOwner')
        self.__currentRoomOwnerInfo['timestamp'] = messageObject.getMessageTimestamp()
        return

    @task
    def syncRoomLieutenants(self):
        if self.__session.isRoomSession():
            room_instance_id = self.__session.getRoomInstanceId()
            if room_instance_id:
                try:
                    room_info = yield self.__serviceProvider.clientGateway.getRoomCardInfo(room_instance_id)
                except networkExceptions:
                    logger.exception('syncRoomLieutenants: getRoomCardInfo failed for %r', room_instance_id)
                else:
                    inner = self.__session.innerSession
                    setLieutenants = getattr(inner, 'setLieutenants', None)
                    if setLieutenants:
                        setLieutenants(room_info.get('lieutenants', []) or [])
                    self.__session.setRoomOwners(room_info.get('roomOwners', []) or [])
                    self.__serviceProvider.eventBus.fire(self, 'SessionWindow.setRoomOwner')

        return

    @__commandHandler('*msg')
    def __msgImpl(self, command, params, messageObject):
        logger.info('action_msgImpl(): command: %r params: %r messageObject: %r', command, params, messageObject)
        if params is None:
            return
        else:
            try:
                message, parta, partb, p1, p2 = params.split()
                self.__receiveMessage(messageObject, message, int(parta), int(partb), int(p1), int(p2))
            except ValueError:
                logger.exception('invalid params passed to *msg: %r', params)

            return

    @task
    def __waitForFurnitureToLoadAndSit(self, pyAv, seatId, furniId):
        timeout = self.__serviceProvider.timeProvider() + 60
        while self.__serviceProvider.timeProvider() < timeout:
            slotId = self.__scenePresenter.getSlotIdForFurnitureId(furniId)
            if slotId:
                product = self.__roomController.getFurnitureProduct(slotId)
                if product:
                    break
            yield Sleep(1)

        pyAv.avatarModel.setSeat((seatId, furniId))
        return

    def ignoreUser(self, userId):
        if userId in self.__session.getParticipantUserIds() and not self.__session.isIgnoredUser(userId):
            self.__session.ignoreUser(userId)
            pyAv = self.pyAvForUserId(userId)
            if pyAv is not None:
                self.removeAvatar(pyAv)
        return

    def unIgnoreUser(self, userId):

        @task
        def unIgnoreUser():
            if userId in self.__session.getParticipantUserIds() and self.__session.isIgnoredUser(userId):
                self.__session.unIgnoreUser(userId)
                info = yield self.__serviceProvider.avatarInfoManager.getAvatarInfo(userId)
                self.addNewAvatar(info, definition=[2999])
            return

        self.attachTask(unIgnoreUser())
        return

    def __receiveMessage(self, messageObject, message, idparta, idpartb, p1, p2):
        if message == 'SeatAssignment':
            userId = messageObject.fromId_
            seatId, furniId = p1, p2
            pyAv = self.pyAvForUserId(userId)
            if pyAv is not None and not pyAv == self.myAvatar:
                taskName = 'seatAssignment%d' % (pyAv.userId_,)
                if furniId:
                    self.__seatAssignmentTasks.runTask(taskName, self.__waitForFurnitureToLoadAndSit(pyAv, seatId, furniId))
                else:
                    self.__seatAssignmentTasks.stopTask(taskName)
                    pyAv.avatarModel.setSeat((seatId, furniId))
        elif message.startswith('TwoPartyAction'):
            pitcher = self.pyAvFromMessage(messageObject)
            self.__animationTasks.runTask('TwoPartyAction %d %d' % (pitcher.userId_, p2), self.__playTwoPartyAnimation(message, pitcher.userId_, p2))
        elif message.startswith('PersonalGestureAction'):
            action = message[message.find(':') + 1:]
            self.__userAccount.recordFact('Solo Animation', {'action': action})
            self.__fireSoloAnimationEvent(action)
            self.__animationTasks.runTask('PersonalGestureAction %d' % (messageObject.fromId_,), self.__playSoloAction(action, messageObject.fromId_))
        else:
            avatar = self.pyAvFromMessage(messageObject)
            if avatar is not None:
                avatar.getSceneObject().receiveMessage(message)
        return

    def __fireSoloAnimationEvent(self, action):
        self.__serviceProvider.eventBus.fire(self, 'SessionWindow.SoloAnimation', {'action': action})
        return

    @task
    def __playSoloAction(self, actionName, pitcherId):
        try:
            action = yield self.__actionList.getSoloActionByOldUrl(actionName)
        except KeyError:
            logger.error('Unknown action %r', actionName)
            return

        star_use, productId = action['pitcherAction'].split()
        productUrl = 'product://%d/index.xml' % (int(productId),)
        if action.get('requiresVIP'):
            pitcherInfo = yield self.__serviceProvider.avatarInfoManager.getAvatarInfo(pitcherId)
            if not int(pitcherInfo['hasVIPPass']):
                return
        yield self.__loadAndTriggerAvatarActions(actionName, productUrl, pitcherId, '', '', 0)
        return

    @property
    def actionList(self):
        return self.__actionList

    def _ignore_two_party_VIP_action_triggered_by_non_VIP(self, actionInfo, pitcherInfo, catcherInfo):
        return actionInfo.get('requiresVIP', False) and not bool(int(pitcherInfo.get('hasVIPPass', False)))

    def _ignore_two_party_AP_action_when_not_AP(self, actionInfo, pitcherInfo, catcherInfo):
        return actionInfo.get('requiresAP', False) and not self.__userAccount.hasAccessPass()

    @task
    def _block_blocked_VIP_action(self, actionList, action, actionInfo, catcherId, catcherInfo, pitcherId):
        if bool(int(catcherInfo.get('hasVIPPass', False))) and actionList.hasBlock(action):
            try:
                result = yield self.__userAccount.shouldUserBlockAction(catcherId, action[1:], pitcherId)
            except networkExceptions as e:
                logger.error('shouldUserBlockAction returned URLError: %s' % e)
                yield Return(None)

            if result and result['block']:
                logger.info('Two-party action blocked!')
                actionInfo = yield actionList.getBlock(action)
        yield Return(actionInfo)
        return

    @task
    def _ignore_unwanted_two_party_action(self, actionInfo, pitcherUserId, catcherUserId):
        if not self.__userAccount.getImvuConfigClientString('client.RENEW_Coop') == 'active':
            yield Return(False)
        catcherAvModel = self.pyAvForUserId(catcherUserId).avatarModel
        prefs = yield self._cachedTwoPartyActionPref(pitcherUserId, catcherAvModel)
        if prefs is None:
            yield Return(True)
        prefName = 'action.' + actionInfo['id'][1:]
        yield Return(not bool(prefs.get(prefName, '1')))
        return

    @task
    def __playTwoPartyAnimation(self, message, pitcherId, catcherId):
        logger.info('__playTwoPartyAnimation(): pitcherId: %r catcherId: %r message: %r', pitcherId, catcherId, message)
        if pitcherId == catcherId:
            return
        try:
            catcherInfo = yield self.__serviceProvider.avatarInfoManager.getAvatarInfo(catcherId)
            pitcherInfo = yield self.__serviceProvider.avatarInfoManager.getAvatarInfo(pitcherId)
        except Exception:
            logger.error('Unknown customer ID %r for two-party action', catcherId)
            return

        try:
            _, action = message.split(':', 1)
        except ValueError:
            return

        actionList = self.__actionList
        try:
            actionInfo = yield actionList.getTwoPartyActionByPitcherAction(action)
        except KeyError:
            return

        if self._ignore_two_party_VIP_action_triggered_by_non_VIP(actionInfo, pitcherInfo, catcherInfo):
            return
        if self._ignore_two_party_AP_action_when_not_AP(actionInfo, pitcherInfo, catcherInfo):
            return
        if (yield self._ignore_unwanted_two_party_action(actionInfo, pitcherId, catcherId)):
            return
        actionInfo = yield self._block_blocked_VIP_action(actionList, action, actionInfo, catcherId, catcherInfo, pitcherId)
        if not actionInfo:
            return
        self.__userAccount.recordFact('Cooperative Animation', {'pitcher': pitcherId, 
           'catcher': catcherId, 
           'action': (actionInfo['pitcherAction'])})
        logger.info('__playTwoPartyAnimation(): final actionInfo: %r', actionInfo)
        yield self.__loadAndTriggerAvatarActions(actionInfo['pitcherAction'], actionInfo['pitcherActionUrl'], pitcherId, actionInfo['catcherAction'], actionInfo['catcherActionUrl'], catcherId)
        self.__serviceProvider.eventBus.fire(self, 'PlayedCoopAction', {'pitcher': pitcherId, 
           'catcher': catcherId, 
           'action': actionInfo})
        return

    def __recordChangeSeatFact(self, seatNumber, furniInstanceId):
        params = {'seat': seatNumber}
        if self.__roomController.roomPid:
            params['room'] = self.__roomController.roomPid
        slotId = self.__scenePresenter.getSlotIdForFurnitureId(furniInstanceId)
        if slotId:
            product = self.__roomController.getFurnitureProduct(slotId)
            if product:
                flashAsset = product.getFlashAsset()
                if flashAsset:
                    params['flashAsset'] = flashAsset['Name']
        self.__userAccount.recordFact('Change Seat', params)
        return

    def __isInShop(self):
        shopTogetherMode = self.__modeManager.getMode(imvu.mode.ShopTogetherMode)
        shopMode = self.__modeManager.getMode(imvu.mode.ShopMode)
        activeMode = self.__modeManager.getActiveMode()
        if activeMode is shopTogetherMode:
            return True
        if activeMode is shopMode:
            return True
        return False

    @__commandHandler('*hiResSnap')
    @__commandHandler('*hiressnap')
    def __hiResSnapshot(self, command, params, messageObject):
        if self.__isInShop() and not self.__userAccount.isAdmin():
            return
        if messageObject.fromId_ == self.__pilotUserId:
            pixmap = self.__sceneWindow.avatarWindow.takeSnapshot(self.__sceneWindow.avatarWindow.fieldOfView)
            img = Image.fromstring('RGBA', (pixmap.width, pixmap.height), pixmap.data).convert('RGB')
            with self.__serviceProvider.desktopFileSystem.file(self.__serviceProvider.desktopFileSystem.pickNextFilenameInSeries('hiResSnapshot', '.png'), 'w') as f:
                img.save(f, format='png')
            self.__userAccount.recordFact('Used_HiResSnap', {})
        return

    @__commandHandler('*hiResNoBg')
    @__commandHandler('*hiResnobg')
    @__commandHandler('*hiresnobg')
    def __hiResSnapshotNoBg(self, command, params, messageObject):
        if self.__isInShop() and not self.__userAccount.isAdmin():
            return
        if messageObject.fromId_ == self.__pilotUserId:
            pixmap = self.__sceneWindow.avatarWindow.takeSnapshotOfAvatars(self.__sceneWindow.avatarWindow.fieldOfView)
            img = Image.fromstring('RGBA', (pixmap.width, pixmap.height), pixmap.data)
            with self.__serviceProvider.desktopFileSystem.file(self.__serviceProvider.desktopFileSystem.pickNextFilenameInSeries('hiResNoBg', '.png'), 'w') as f:
                img.save(f, format='png')
            self.__userAccount.recordFact('Used_HiResNoBG', {})
        return

    def addNewAvatar(self, avatarInfo, definition, useProductPolicy=None, editedProductId=None):
        userId = avatarInfo['userId']
        seat = (findUnoccupiedSeatNumber(self.avatars, userId), 0)
        logger.info('addNewAvatar(): definition=%r userId=%r seat=%r', definition, userId, seat)
        assertInRelease(isinstance(definition, list))
        avatarModel = imvu.scene.avatarmodel.AvatarModel(avatarInfo['userId'], self.__serviceProvider.eventBus)
        avatarModel.setSeat(seat)
        self.__sceneModel.addAvatarModel(avatarModel)
        avatarPresenter = self.__scenePresenter.getAvatarPresenter(avatarModel)
        assertInRelease(avatarPresenter)
        pyAv = self.__serviceProvider.create(AvatarController, avatarModel=avatarModel, avatarPresenter=avatarPresenter, avatarInfo=avatarInfo, productLoadingHalter=self.avatarProductLoadingHalter, useProductPolicy=useProductPolicy, productLoader=self.__productLoader, editedProductId=editedProductId)
        pyAv.showNameLabel(self.__showingAvatarNameLabels, htmlOverlayFactory=self.__serviceProvider.htmlOverlayFactory)
        self.__serviceProvider.eventBus.register(pyAv, 'ProductsChanged', self.notifyProductChanges)
        self.__serviceProvider.eventBus.register(avatarModel, 'BadProduct', self.onBadProduct)
        self.__avatarControllers.append(pyAv)
        self.__usePidsOnAvatar(pyAv, definition, initialOutfit=True)
        logger.info('<< addNewAvatar(): created pyAv %r', pyAv)
        self.__updateNameTags()
        if self.__userAccount.getImvuConfigClientString('client.RENEW_Coop') == 'active':
            self.retrieveTwoPartyActionPrefs(pyAv)
        return pyAv

    def retrieveTwoPartyActionPrefs(self, pyAv):
        self.attachTask(self.__retrieveTwoPartyActionPrefs(self.__userAccount.getUserId(), pyAv.avatarModel))
        return

    @task
    def __retrieveTwoPartyActionPrefs(self, pitcherUserId, catcherAvModel):
        if catcherAvModel.getUserId() == pitcherUserId:
            yield Return(False)
        url = imvu.network.getServiceDomain() + '/api/avatar_actions_permission.php'
        result = {}
        try:
            args = [('pitcher_id', pitcherUserId),
             (
              'catcher_id', catcherAvModel.getUserId())]
            url = url + '?' + urllib.urlencode(args)
            result = yield imvu.http.securePost(url, None, self.__userAccount.getAuth(), [
             'actions'], self.__serviceProvider.network)
            if 'actions' in result:
                catcherAvModel.setTwoPartyPref(pitcherUserId, result['actions'])
                yield Return(True)
        except networkExceptions as e:
            logger.exception('failed to retrieve two party preferences for user ' + str(catcherAvModel.getUserId()))

        yield Return(False)
        return

    @task
    def _cachedTwoPartyActionPref(self, pitcherUserId, catcherAvModel):
        if not catcherAvModel.hasTwoPartyPref(pitcherUserId):
            if not (yield self.__retrieveTwoPartyActionPrefs(pitcherUserId, catcherAvModel)):
                yield Return(None)
        yield Return(catcherAvModel.getTwoPartyPref(pitcherUserId))
        return

    def __newChatIdListener(self, fromSender, eventName, info):
        logger.info('__newChatIdListener: fromSender: %r eventName: %r info: %r', fromSender, eventName, info)
        self.__serviceProvider.eventBus.fire(self, eventName, info)
        return

    def __joinedChatListener(self, event):
        seat = event.info.get('seat', None)
        oldSeat = self.myAvatar.avatarModel.seat
        if seat is not None:
            if oldSeat != (1, 0):
                self.__session.sendImMessage('*msg SeatAssignment 2 %i %i %i' % (self.__pilotUserId, oldSeat[0], oldSeat[1]))
                self.updateChatSeat(oldSeat[0], oldSeat[1])
                self.updateChatOutfit()
            else:
                self.setSeat(self.myAvatar, (seat, 0))
                self.updateChatSeat(seat, 0)
                self.updateChatOutfit()
        # IMVU room antibot patch
        session = self.__session
        inner = getattr(session, 'innerSession', None)
        if inner is not None:
            session = inner
        self.__serviceProvider.eventBus.fire(
            self,
            'SessionWindow.AntibotProtectionStatus',
            im.antibot._protection_status_info(session),
        )
        return

    def __antibotBootedListener(self, event):
        info = dict(event.info)
        if 'boots' not in info:
            info['boots'] = im.antibot.get_boot_log(event.sender)
        self.__serviceProvider.eventBus.fire(self, 'SessionWindow.AntibotBooted', info)
        return

    def __antibotProtectionListener(self, event):
        info = event.info or im.antibot._protection_status_info(event.sender)
        self.__serviceProvider.eventBus.fire(self, 'SessionWindow.AntibotProtectionStatus', info)
        return

    def __handleParticipantsUpdated(self, event):
        return

    def __participantJoinedListener(self, event):
        info = event.info
        logger.info('__participantJoinedListener(): info=%r', info)
        userId = int(info['userId'])
        if self.isRoomOwner(userId):
            self._stopPrivateChatClosureTimeout()
        if self.__session.isIgnoredUser(userId):
            logger.info('ignored user joined')
            return
        assertInRelease(userId)
        assertInRelease(not self.pyAvForUserId(userId=userId), userId)
        avatarInfo = info['avatarInfo']
        pyAv = self.addNewAvatar(avatarInfo, definition=[2999])
        if not avatarInfo.hasAPPlus:
            self.__nonAPPUsers.append(userId)
        if not avatarInfo.hasAP:
            self.__nonAPUsers.append(userId)
        info = {'who': (avatarInfo.avatarName), 
           'nameTagColor': (pyAv.nameTagColor), 
           'userId': userId, 
           'hasVIPPass': (avatarInfo.isVIP), 
           'hasAccessPass': (avatarInfo.hasAP)}
        self.__serviceProvider.eventBus.fire(self, 'SessionWindow.ParticipantJoined', info)
        self.broadcastMyState('Other avatar joined chat')
        return

    def __participantLeftListener(self, event):
        info = event.info
        logger.info('__participantLeftListener(): info=%r', info)
        userId = int(info['userId'])
        if not self.__session.isRoomSession() and not self.__session.isLocalChat():
            if self.isRoomOwner(userId):
                changeroom_msg = '*imvu:changeRoom %r' % self.__roomController.roomPid
                logger.info('taking control of room due to owner departure, changeroom_msg: %r session: %s', changeroom_msg, self.__session)
                self.__session.sendImMessage(changeroom_msg)
        if self.__session.isIgnoredUser(userId):
            logger.info('ignored user left')
            return
        pyAv = self.pyAvForUserId(userId=userId)
        assertInRelease(pyAv)
        self.removeAvatar(pyAv=pyAv)
        if userId in self.__nonAPPUsers:
            self.__nonAPPUsers.remove(userId)
        anyOwnersLeft = len(set(self.__session.getRoomOwners()) & set(self.__session.getParticipantUserIds())) > 0
        isClosing = self.isRoomOwner(userId) and self.__session.isPrivate() and self.__session.autoBootWhenOwnerLeaves() and not anyOwnersLeft
        info = {'who': (pyAv.avatarName), 
           'nameTagColor': (pyAv.nameTagColor), 
           'userId': userId, 
           'isClosing': isClosing, 
           'allowLoadNewRoom': (self.__session.allowLoadNewRoom())}
        self.__serviceProvider.eventBus.fire(self, 'SessionWindow.ParticipantLeft', info)
        if isClosing:
            self.__privateChatOwnerLeft.set()
        return

    def _stopPrivateChatClosureTimeout(self):
        self.__secondsUntilPrivateChatCloses = 120
        self.__privateChatOwnerLeft.clear()
        return

    @task
    def _handlePrivateChatOwnerAbsent(self):
        sleepTime = 30
        if not (self.__session.isPrivate() and self.__session.isRoomSession()):
            return
        while True:
            yield self.__privateChatOwnerLeft.wait()
            if self.__secondsUntilPrivateChatCloses <= 0:
                self.dispose()
                return
            if self.__secondsUntilPrivateChatCloses <= 10:
                message = 'This session will close in %s seconds.\n'
                if self.__session.allowLoadNewRoom():
                    message += "\nLoad one of your rooms before it's too late!"
                self.__displayCenteredFafMessage(10, 'Chat Closing', message % self.__secondsUntilPrivateChatCloses)
                sleepTime = self.__secondsUntilPrivateChatCloses
                self.__secondsUntilPrivateChatCloses = 0
            else:
                message = 'The owner has left their session. '
                if self.__session.allowLoadNewRoom():
                    message += 'This session\n\nwill close in %d seconds unless you load your room.'
                else:
                    message += 'This session\n\nwill close in %d seconds.'
                self.__displayCenteredFafMessage(10, 'Session Closing', message % self.__secondsUntilPrivateChatCloses)
                if self.__secondsUntilPrivateChatCloses <= 30:
                    sleepTime = 20
                else:
                    sleepTime = 30
                self.__secondsUntilPrivateChatCloses -= sleepTime
            yield Sleep(sleepTime)

        return

    def pyAvFromMessage(self, messageObject):
        userId = messageObject.getMessageFromId()
        assertInRelease(userId, userId)
        pyAv = self.pyAvForUserId(userId=userId)
        assertInRelease(pyAv)
        return pyAv

    def maybePlayChatCommand(self, cmdName, pyAv):
        logger.debug('maybePlayChatCommand(): cmdName: %r pyAv: %r', cmdName, pyAv)
        pyAv.triggerActionByName(cmdName)
        self.__roomController.room.triggerActionByName(cmdName)
        return

    @__commandHandler('*imvu:trigger')
    def __imvuTriggerImpl(self, command, params, messageObject):
        if not params:
            return
        pyAv = self.pyAvFromMessage(messageObject)
        subCommands = params.split(' ')
        for c in subCommands:
            if c:
                self.maybePlayChatCommand(c, pyAv)

        return

    @__commandHandler('*imvu:untrigger')
    def __imvuTriggerImpl(self, command, params, messageObject):
        if not params:
            return
        pyAv = self.pyAvFromMessage(messageObject)
        subCommands = params.split(' ')
        for c in subCommands:
            if c:
                pyAv.untriggerActionByName(c)
                self.__roomController.room.untriggerActionByName(c)

        return

    @__messageHandler
    def __addToChatHistory(self, msg):
        if not msg.message_.startswith('*imvu:'):
            if msg.getMessageFromId():
                self.__chatHistory.add(self.pyAvFromMessage(msg).avatarName, msg.message_)
            else:
                self.__chatHistory.add('Admin', msg.message_)
        return

    @__messageHandler
    def __lookForChatCommands(self, msg):
        if not msg.getMessageFromId():
            return
        pyAv = self.pyAvFromMessage(msg)
        assertInRelease(pyAv)

        def removeLeadingSlashes(w):
            return re.sub('^/+', '', w)

        def wordsWithSlashes(words):
            result = []
            for w in words:
                if not w.startswith('/'):
                    continue
                result.append(removeLeadingSlashes(w))

            return result

        words = msg.message_.split()
        if len(words) > 1:
            words = wordsWithSlashes(words)
        else:
            words = [
             removeLeadingSlashes(words[0])]
        words = [w for w in words if w]
        for word in words:
            self.maybePlayChatCommand(cmdName=word, pyAv=pyAv)

        return

    @__messageHandler
    def __newMsgImpl(self, msg):
        logger.debug('handler_newMsgImpl: %r', msg)
        if msg.getMessageFromId():
            pyAv = self.pyAvFromMessage(msg)
        else:
            pyAv = None
        if msg.message_.startswith('*imvu:'):
            logger.debug('Message %r is a *imvu:.  Suppressing.', msg)
            return
        else:
            info = {'who': (pyAv.avatarName if pyAv else 'Admin'), 'nameTagColor': (pyAv.nameTagColor if pyAv else SELF_AVATAR_COLOR), 
               'message': (msg.message_), 
               'userId': (msg.fromId_), 
               'to': (msg.toId), 
               'hasVIP': (pyAv.avatarInfo.isVIP if pyAv else True), 
               'index': (self.__chatHistory.index()), 
               'outgoingMessageId': (msg.outgoingMessageId)}
            if msg.toId:
                info.update({'toName': (self.pyAvForUserId(msg.toId).avatarName)})
            self.__serviceProvider.eventBus.fire(self, 'SessionWindow.ReceivedMessage', info)
            if msg.fromId_ != self.__pilotUserId and pyAv:
                pyAv.addBubble(msg.message_)
            return

    def __handleMessageDeliveryNotification(self, outgoingMessageId):
        logger.debug('__handleMessageDeliveryNotification: %r', outgoingMessageId)
        self.__serviceProvider.eventBus.fire(self, 'SessionWindow.MessageDelivered', {'outgoingMessageId': outgoingMessageId})
        return

    def getPidsForOutfitSnapshot(self):
        pyAv = self.myAvatar
        return [p.getProductId() for p in pyAv.allProductsWorn() if p.isClothingProduct() and not p.isMoodProduct()]

    @__commandHandler('*imvu:activateMusic')
    def __activateMusicImpl(self, command, params, messageObject):
        self.__serviceProvider.eventBus.fire(self, 'ActivateMusic')
        return

    @__commandHandler('*imvu:deactivateMusic')
    def __deactivateMusicImpl(self, command, params, messageObject):
        self.__serviceProvider.eventBus.fire(self, 'DeactivateMusic')
        return

    @__commandHandler('*undo')
    def __undo(self, command, params, messageObject):
        pyAv = self.pyAvFromMessage(messageObject)
        if pyAv.userId == self.__pilotUserId:
            pyAv.undo()
        return

    @__commandHandler('*redo')
    def __redo(self, command, params, messageObject):
        pyAv = self.pyAvFromMessage(messageObject)
        if pyAv.userId == self.__pilotUserId:
            pyAv.redo()
        return

    @__commandHandler('*imvu:try')
    @__commandHandler('*imvu:tryForUndo')
    def __tryImpl(self, command, params, messageObject):
        if params is None:
            return
        else:
            pyAv = self.pyAvFromMessage(messageObject)
            productId, isOutfit = (params.split() + [None])[:2]
            if productId in pyAv.wornProductIds:
                return
            if not isOutfit:
                self.__usePidsStrOnAvatar(pyAv=pyAv, pids_str=productId)
            try:
                productId = int(productId)
            except ValueError:
                logger.info('invalid pid %r', productId)
                return

            if command != '*imvu:tryForUndo':
                self.attachTask(self.displayShoppingEvent(byAvatar=pyAv, productId=productId, eventName='SessionWindow.TryProduct'))
            return

    @__commandHandler('*imvu:recommend')
    def __recommendImpl(self, command, params, messageObject):
        self.attachTask(self.checkAndDisplayShoppingEvent(params, messageObject, 'SessionWindow.RecommendProduct'))
        return

    @__commandHandler('*imvu:purchase')
    def __purchaseImpl(self, command, params, messageObject):
        self.attachTask(self.checkAndDisplayShoppingEvent(params, messageObject, 'SessionWindow.PurchaseProduct'))
        return

    @__commandHandler('*imvu:gift')
    def __purchaseImpl(self, command, params, messageObject):
        self.attachTask(self.checkAndDisplayShoppingEvent(params, messageObject, 'SessionWindow.GiftProduct'))
        return

    @task
    def checkAndDisplayShoppingEvent(self, params, messageObject, eventName):
        shopTogetherMode = self.__modeManager.getMode(imvu.mode.ShopTogetherMode)
        activeMode = self.__modeManager.getActiveMode()
        if activeMode is not shopTogetherMode:
            return
        else:
            shopTogetherRoomPid = shopTogetherMode.getDefaultRoomPid()
            if params is None:
                yield Return()
            pyAv = self.pyAvFromMessage(messageObject)
            productId = params
            try:
                productId = int(productId)
            except ValueError:
                logger.info('invalid pid %r', productId)
                yield Return()

            if productId == shopTogetherRoomPid:
                yield Return()
            self.attachTask(self.displayShoppingEvent(byAvatar=pyAv, productId=productId, eventName=eventName))
            return

    @task
    def displayShoppingEvent(self, byAvatar, productId, eventName, toAvatar=None):
        myAv = self.pyAvForUserId(self.__userAccount.getUserId())
        productWorn = int(productId) in myAv.wornProductIds
        products = yield self.__serviceProvider.productInfoManager.getProductsByIds([productId])
        if toAvatar:
            toAvatarName = toAvatar.avatarName
            toAvatarUserId = toAvatar.userId
        else:
            toAvatarName = ''
            toAvatarUserId = None
        for pi in products:
            if pi.get('products_mature', 'Y') != 'N' and self.__userAccount.isTeen():
                continue
            if pi.get('products_mature', '4') == '4' and not self.__userAccount.hasAccessPassPlus():
                continue
            info = {'who': (byAvatar.avatarName), 
               'nameTagColor': (byAvatar.nameTagColor), 
               'userId': (byAvatar.userId), 
               'creatorName': (HTMLParser.HTMLParser().unescape(pi['manufacturers_name'])), 
               'productName': (HTMLParser.HTMLParser().unescape(pi['products_name'])), 
               'productMature': (pi['products_mature']), 
               'productId': (pi['products_id']), 
               'productOwned': (self.__userAccount.getInventoryState().ownedPid(pi['products_id'])), 
               'productImage': (pi['products_image']), 
               'productWorn': productWorn, 
               'purchasable': (pi.get('is_purchasable', True)), 
               'to': toAvatarName, 
               'recipientUserId': toAvatarUserId}
            self.__serviceProvider.eventBus.fire(self, eventName, info)

        return

    @__commandHandler('*use')
    @__commandHandler('*putOn')
    def __putOnImpl(self, command, params, messageObject):
        if params is not None:
            pyAv = self.pyAvFromMessage(messageObject)
            self.__usePidsStrOnAvatar(pyAv=pyAv, pids_str=params)
            self.updateChatOutfit()
        self.attachTask(self.checkAndDisplayShoppingEvent(params, messageObject, 'SessionWindow.TryProduct'))
        return

    def tryOnOutfit(self, pidsString, isOutfit=True):
        if pidsString is not None:
            self.applyOutfit(self.myAvatar, pidsString, isOutfit, True)
        return

    @__commandHandler('*putOnOutfit')
    def __putOnOutfitImpl(self, command, params, messageObject):
        logger.info('putOnOutfit(): params: %r messageObject: %r', params, messageObject)
        if params is not None:
            pyAv = self.pyAvFromMessage(messageObject)
            if pyAv.userId == self.__pilotUserId:
                self.__userAccount.recordFact('Put On Outfit', {})
            self.applyOutfit(pyAv, params)
            if pyAv.userId == self.__pilotUserId:
                self.updateChatOutfit()
        return

    def __cancelOutfitPhoto(self):
        if self.__photoWidget and self.__photoWidget.isTakingPhoto() and self.__photoWidget.getPhotoType() == 'outfit':
            self.__photoWidget.cancel()
        return

    def applyOutfit(self, pyAv, pids_str, isOutfit=True, trialAuth=False):
        logger.info('applyOutfit(): %r', pids_str)
        if pyAv == self.myAvatar:
            self.__cancelOutfitPhoto()
        pids = self.__parsePidsStr(pids_str)
        pyAv.setOutfit(pids, isOutfit, trialAuth)
        return

    def tryOnRoomBundle(self, bundlePid):
        self.attachTask(self.__applyRoomBundle(bundlePid, True))
        return

    @task
    def __applyRoomBundle(self, bundlePid, trialAuth=False):
        state = yield self.__userAccount.getRoomStateForBundleEx(bundlePid)
        if state:
            state['room_state']['room_info']['room_instance_id'] = ''
            roomState = self.__serviceProvider.roomStateManager.createLocalRoomState(localState=state)
            yield self.__loadRoom(self.__pilotUserId, int(state['room_state']['room_info']['room_pid']), roomState, None, trialAuth)
            self.broadcastMyState('loaded room bundle')
        return

    @task
    def __takeOffImpl(self, command, params, messageObject):
        logger.info('takeoffImpl(): command: %r params: %r messageObject: %r', command, params, messageObject)
        pyAv = self.pyAvFromMessage(messageObject)
        if not params:
            logger.error('takeoffImpl: no params')
            return
        for p in params.split():
            try:
                yield self.removeProductById(pyAv=pyAv, productId=int(p))
            except ValueError:
                logger.exception('takeoffImpl(): bad param: %r', p)

        if pyAv.userId == self.__pilotUserId:
            self.updateChatOutfit()
        return

    @__commandHandler('*takeOff')
    @__commandHandler('*remove')
    def __takeoffImplLauncher(self, command, params, messageObject):
        self.attachTask(self.__takeOffImpl(command, params, messageObject))
        return

    @__commandHandler('*removeMood')
    def __takeoffMoodImpl(self, command, params, messageObject):
        logger.info('takeoffMoodImpl(): command: %r params: %r messageObject: %r', command, params, messageObject)
        pyAv = self.pyAvFromMessage(messageObject)
        products = pyAv.allProductsWorn()
        remove = []
        for pi in products:
            if pi.isMoodProduct():
                remove.append(pi.getProductId())

        pyAv.removePids(remove)
        if pyAv.userId == self.__pilotUserId:
            self.updateChatOutfit()
        return

    @activemethod
    def inviteToChat(self, userId):
        if self.__session.sessionIsFull():
            self.__modeManager.startNewPrivateChat(userId)
        else:
            isSafe = yield self.showMessageIfInviteIsNotSafe(userId)
            if isSafe:
                self.__session.inviteToChat(inviteeId=userId)
        return

    @task
    def showMessageIfInviteIsNotSafe(self, userId):
        if not self.__roomController.roomState:
            yield Return(False)
        roomPid = yield self.__roomController.roomState.getRoomProductId()
        if not roomPid:
            yield Return(False)
        contents = yield self.__roomController.roomState.getRoomContents()
        result = yield im.meet.checkInviteSafety(self.__serviceProvider, userId, roomPid, contents)
        if result:
            self.__displayCenteredFafMessage(10, 'Invite Declined', result)
            yield Return(False)
        yield Return(True)
        return

    def __displayCenteredFafMessage(self, duration, title, message, height=90, closeable=False):
        msg_info = {}
        msg_info['duration'] = duration
        msg_info['dialogText'] = '{CloseBox}' + str(int(closeable)) + '{/CloseBox}'
        msg_info['dialogText'] += '{WindowType}Modal{/WindowType}'
        msg_info['dialogText'] += '{PointSize}18{/PointSize}'
        msg_info['dialogText'] += '{Timeout}9000{/Timeout}'
        msg_info['dialogText'] += '{Bold}%s{/Bold}\n\n\n\n' % title
        msg_info['dialogText'] += message + '\n\n'
        msg_info['updateHeight'] = height
        self.__fafManager_.setFafMessageInfo(title, msg_info)
        return

    @__commandHandler('*resume')
    def __resume(self, command, params, messageObject):
        self.__setRoomOwner(messageObject)
        return

    @__commandHandler('*accept')
    def __accept(self, command, params, messageObject):
        try:
            userId = int(params)
        except (ValueError, TypeError):
            logger.exception('bad params to *accept: %r', params)
            return

        if userId == self.__pilotUserId:
            self.__currentRoomOwnerInfo['userId'] = -1
        return

    @__commandHandler('*uid')
    @__commandHandler('*uploadSnap')
    @__commandHandler('*saveOutfit')
    @__commandHandler('*saveoutfit')
    @__commandHandler('*snap')
    @__commandHandler('*seat')
    def __swallowLegacyCommand(self, command, params, messageObject):
        return

    @property
    def __sessionEventListeners(self):
        return [
         (
          'ParticipantsUpdated', self.__handleParticipantsUpdated),
         (
          'ParticipantJoined', self.__participantJoinedListener),
         (
          'ParticipantLeft', self.__participantLeftListener),
         (
          'Session.End', self.__sessionEndListener),
         (
          'JoinedChat', self.__joinedChatListener),
         (
          'AntibotBooted', self.__antibotBootedListener),
         (
          'AntibotProtectionStatus', self.__antibotProtectionListener),
         (
          'ControlMessage', self.__controlMessageListener),
         (
          'DisconnectionDetected', self.__handleDisconnection)]

    def __sessionEndListener(self, event):
        if event.sender != self.__session:
            return
        self.dispose()
        return

    def __handleDisconnection(self, event):
        if event.sender != self.__session:
            return
        self.dispose()
        return

    def changeImSession(self, newImSession):
        logger.info('changeImSession(%s) - avatars %r', newImSession, newImSession.getParticipantUserIds())
        oldImSession = self.__session.innerSession
        self.__session.changeSession(newImSession)
        if self.__session.isRoomSession():
            self.__resetRoomFromDefinition()
            if oldImSession and oldImSession != newImSession:
                self.setSeat(pyAv=self.myAvatar, seat=(0, 0))
        return

    def broadcastMyState(self, reason):
        self.__serviceProvider.eventBus.fire(self, 'BroadcastSessionState', {'reason': reason})
        return

    @task
    def myState(self):
        try:
            pyAv = self.myAvatar
        except Exception:
            yield Return([])

        state = []
        pids = list(pyAv.stateAsPids())
        logger.info('myState: %r %r', pids, pyAv.loadingPids)
        pids.extend(pyAv.loadingPids)
        if pids:
            state.extend(['*use %s' % (' ').join(map(str, pids))])
        if self.isRoomOwner(pyAv.userId) and self.__roomController.isDriver():
            starState = yield self.__roomController.stateAsStarCommands()
            state.extend(starState)
        seatNumber, furniInstanceId = pyAv.avatarModel.seat
        if seatNumber is not None and furniInstanceId is not None:
            state.append('*msg SeatAssignment 0 %s %s %s' % (pyAv.userId_, seatNumber, furniInstanceId))
        yield Return(state)
        return

    def getSceneJsonState(self, filterDefaultValues=True, filterIds=False):
        state = self.__sceneWindow.avatarWindow.getRootSceneObject().getJsonState(filterDefaultValues, filterIds)
        return state

    def copyChatLog(self):
        self.__serviceProvider.platform.setClipboardText(self.__chatHistory.get())
        return

    @property
    def chatHistory(self):
        return self.__chatHistory

    def __handleFlashUrlRequest(self, virtualUrl, result):
        match = re.match('^http://product\\.virtual\\.imvu\\.com/([0-9]+)/(.*)$', virtualUrl, 0)
        if match:
            return self.__handleProductFlashUrl(match, virtualUrl, result)
        if virtualUrl.startswith('http://program.virtual.imvu.com'):
            return self.__handleProgramFlashUrl(virtualUrl, result)
        return False

    def __handleProductFlashUrl(self, match, virtualUrl, result):
        productId, assetName = match.groups()
        productId = int(productId)
        matchingProducts = [productInstance for productInstance in self.__scenePresenter.getProductsInUse() if productId == productInstance.getProductId()]
        if not matchingProducts:
            return False
        productInstance = matchingProducts[0]

        @task
        def loadProductAsset():
            try:
                data, _ = yield productInstance.getMergedAsset(assetName, tag='original')
            except Exception:
                logger.exception('Failed to resolve flash URL request: %r', virtualUrl)
            else:
                result.write(data)

            return

        self.attachTask(loadProductAsset())
        return True

    def __handleProgramFlashUrl(self, virtualUrl, result):
        scheme, netloc, path, query, fragment = urlparse.urlsplit(virtualUrl)
        if path.startswith('/'):
            path = path[1:]
        data = self.__serviceProvider.programFileSystem.file(path, 'rb').read()
        result.write(data)
        return True

    @property
    def scenePresenter(self):
        return self.__scenePresenter

    def isRoomFullyLoaded(self, notFullyLoadedList=[]):
        if self.__roomController is None or not self.__roomController.isIdle() or not self.__scenePresenter.isFullyLoaded() or not self.__roomController.isFullyLoaded():
            notFullyLoadedList.append('ImSessionWindow.__roomController is %r' % self.__roomController)
            return False
        else:
            return True

    def isFullyLoaded(self, notFullyLoadedList=[]):
        if not self.isRoomFullyLoaded(notFullyLoadedList):
            return False
        for avatar in self.avatars:
            if not avatar.isFullyLoaded(notFullyLoadedList):
                notFullyLoadedList.append('ImSessionWindow.avatar %r' % avatar)
                return False

        return True

    @task
    def waitForConfiguringIdle(self):
        if not self.configIdleEvent.isSet():
            yield self.configIdleEvent.wait()
            yield Return()
        self.configIdleEvent.clear()
        while True:
            if self.__disposed:
                yield Return()
            if self.isFullyLoaded():
                self.configIdleEvent.set()
                yield Return()
            yield Sleep(0.25)

        return

    def __getTotalLoadedProducts(self):
        loadedPids = set()
        for av in self.__avatarControllers:
            if not av.dirty():
                loadedPids.update(av.stateAsPids())

        if not self.__roomController.dirty():
            loadedPids.update(self.__roomController.stateAsPids())
        return len(loadedPids)

    def __logAvatarAndRoomState(self):
        if not self.isDisposed():
            pids = set()
            for av in self.__avatarControllers:
                pids.update(av.stateAsPids())

            pids.update(self.__scenePresenter.getPidsInUse())
            if pids:
                logger.info('Current avatar and room state: total %r, pid %s', len(pids), sorted(pids))
        return

    def __listenPresenceProductsAdded(self, presence, product):
        self.useLoadedProduct(pyAv=presence, product=product)
        return

    def notifyChatMessage(self, message, to=0):
        if not self.__commandManager.isCommand(message):
            userAccount = self.__userAccount
            if userAccount.isPasswordInString(message):
                self.__serviceProvider.dialogManager.showModal(self.window, imvu.dialog.PasswordSecurityAlertDialog())
                return
            logger.info('notifyChatMessage: %r', message)
            userAccount.recordFactOnlyOnce('Type a Bubble', {})
            self.__serviceProvider.eventBus.fire(self, 'SessionWindow.UserText', {'text': message})
        self.__session.sendImMessage(message, to)
        self.macroManager.handleMacroExpansion(self.__session, message, bodyPatternId=self.myAvatarBodyPatternId())
        return

    def cancelChatMessage(self, outgoingMessageId):
        self.__session.cancelMessage(outgoingMessageId)
        return

    def initiateNewChat(self, roomInstanceId, roomName):
        pyAv = self.pyAvForUserId(userId=self.__userAccount.getUserId())
        info = {'roomName': roomName, 
           'roomInstanceId': roomInstanceId, 
           'who': (pyAv.avatarName), 
           'nameTagColor': (pyAv.nameTagColor), 
           'userId': (pyAv.userId), 
           'hasVIP': (pyAv.avatarInfo.isVIP)}
        self.__serviceProvider.eventBus.fire(self, 'SessionWindow.InitiateNewChat', info)
        return

    def makeFurniMenu(self, furniId):

        def makeSetManip(mode):
            return (lambda : self.__sceneWindow.avatarWindow.setFurniManipulationModeSetting(mode))

        fmm = avatarwindow.FurniManipulationMode
        menu_list = [imvu.menu.Item('Explore', makeSetManip(fmm.FurniManipulationModeNull)),
         imvu.menu.Item('Move', makeSetManip(fmm.FurniManipulationModeMove)),
         imvu.menu.Item('Rotate', makeSetManip(fmm.FurniManipulationModeRotate)),
         imvu.menu.Item('Scale', makeSetManip(fmm.FurniManipulationModeScale)),
         imvu.menu.Item('Copy', makeSetManip(fmm.FurniManipulationModeClone)),
         imvu.menu.Item('Reset', makeSetManip(fmm.FurniManipulationModeStraighten))] + [
         imvu.menu.Item('Lock', makeSetManip(fmm.FurniManipulationModeLock)),
         imvu.menu.Item('Delete', makeSetManip(fmm.FurniManipulationModeZap)),
         imvu.menu.Sep,
         imvu.menu.CheckBox('Snap Rotation', (lambda : self.__sceneWindow.avatarWindow.snapRotationsModeOn()), (lambda mode: self.__sceneWindow.avatarWindow.setSnapRotationsModeOn(bool(mode))))]
        return menu_list

    def __trackPopupMenu(self, position, menuDesc):
        self.__serviceProvider.menuFactory.trackPopupMenu(menuDesc, self.__sceneWindow.avatarWindow.getRenderedWindow(), position=position)
        return

    def getProductsDownloadSize(self, products):
        sizes = {}
        for pi in products:
            sizes.update(pi.getMinimumDownloadSizes())

        return sum(sizes.values())

    def notify2(self, notification, p1, p2):
        logger.info('Received notify2: %s p1 %s p2 %s', notification, p1, p2)
        if ':' in notification:
            notification, textParam = notification.split(':', 1)
        else:
            textParam = None
        if notification == u'AvatarWindowNotificationClickOnNameTag':
            userId = p1
            if userId:
                imvu.dialog.showAvatarCard(self.window, self.__serviceProvider, self.__modeManager, self.__userAccount, userId, {}, extra_args={'isChattingWithAvatar': True})
        elif notification == u'AvatarWindowNotificationLeftClickOnUrlBubble':
            self.__serviceProvider.browser.launchUrl(textParam)
        else:
            assertInRelease(False, 'Received unknown notify2: %s p1 %s p2 %s' % (notification, p1, p2))
        return

    def __logAvatarSize(self):
        currentSize = self.getAvatarDownloadSize(self.myAvatar)
        if currentSize and currentSize != self.__myAvatarDownloadSize:
            self.__myAvatarDownloadSize = currentSize
            self.attachTask(self.__userAccount.updateAvatarDownloadSize(currentSize))
        return

    def handleClickOnFurniture(self, localPos, furniInstanceId):
        self.__trackPopupMenu(localPos, self.makeFurniMenu(furniInstanceId))
        return

    def getProductsInScene(self):
        roompidsfull = map(str, sorted(self.__scenePresenter.getPidsInUse()))
        i = 0
        while i < len(roompidsfull):
            if roompidsfull.count(roompidsfull[i]) > 1:
                count = 1
                while roompidsfull.count(roompidsfull[i]) > 1:
                    roompidsfull.remove(roompidsfull[i])
                    count += 1

                roompidsfull[i] = roompidsfull[i] + 'x' + str(count)
            i += 1

        pids = {'room': ((';').join(roompidsfull))}
        for avatar in self.avatars:
            if bool(avatar.avatarInfo.get('is_proxy', False)):
                continue
            avatarPidsFull = map(str, sorted(avatar.pidsInUse))
            i = 0
            while i < len(avatarPidsFull):
                if avatarPidsFull.count(avatarPidsFull[i]) > 1:
                    count = 1
                    while avatarPidsFull.count(avatarPidsFull[i]) > 1:
                        avatarPidsFull.remove(avatarPidsFull[i])
                        count += 1

                    avatarPidsFull[i] = avatarPidsFull[i] + 'x' + str(count)
                i += 1

            pids['avatar%d' % avatar.userId_] = (';').join(avatarPidsFull)

        return pids

    @task
    def hasAPProductsInScene(self):
        pids = self.__scenePresenter.getPidsInUse()
        for avatar in self.avatars:
            pids.extend(avatar.pidsInUse)

        products = yield self.__serviceProvider.productInfoManager.getProductsByIds(pids)
        for pi in products:
            if pi['products_mature'] == 'Y':
                yield Return(True)

        yield Return(False)
        return

    @task
    def hasAPPlusProductsInScene(self):
        pids = self.__scenePresenter.getPidsInUse()
        for avatar in self.avatars:
            pids.extend(avatar.pidsInUse)

        products = yield self.__serviceProvider.productInfoManager.getProductsByIds(pids)
        for pi in products:
            if pi['products_mature'] == '4':
                yield Return(True)

        yield Return(False)
        return

    @task
    def hasUnpublishedProductsInScene(self):
        pids = self.__scenePresenter.getPidsInUse()
        for avatar in self.avatars:
            pids.extend(avatar.pidsInUse)

        products = yield self.__serviceProvider.productInfoManager.getProductsByIds(pids)
        for pi in products:
            if pi['products_id'] == imvu.create.FAKE_PID:
                yield Return(True)
            if 'is_published' not in pi or pi['is_published'] == '0' and not self.__productAuthorizer.isAutoAuthorizedPid(pi['products_id']):
                self.__serviceProvider.productInfoManager.productInfoCache.clearProduct(pi['products_id'])
                products2 = yield self.__serviceProvider.productInfoManager.getProductsByIds([pi['products_id']])
                if len(products2) > 0:
                    pi = products2[0]
                    if 'is_published' in pi:
                        if pi['is_published'] == '0':
                            yield Return(True)

        yield Return(False)
        return

    @task
    def viewProductsInScene(self):
        params = self.getProductsInScene()
        self.__serviceProvider.browser.launchNamedUrl('view_products_in_scene', params)
        return

    def handleRightClickOnBackground(self, localPos):

        def launchViewProductsInScene():
            self.attachTask(self.viewProductsInScene())
            return

        self.__trackPopupMenu(localPos, [
         imvu.menu.Item('View products in this scene', launchViewProductsInScene),
         imvu.menu.Item('Copy chat log', self.copyChatLog),
         imvu.menu.Item('Paste', self.doPaste, enabled=bool(self.__serviceProvider.platform.getClipboardText()))])
        return

    def doPaste(self):
        text = self.__serviceProvider.platform.getClipboardText()
        if text:
            self.__sceneWindow.avatarWindow.paste(text, False)
        return

    def doCopy(self):
        text = self.__sceneWindow.avatarWindow.copy()
        if text:
            self.__serviceProvider.platform.setClipboardText(text)
        return

    def pyAvForUserId(self, userId):
        assertInRelease(userId)
        for pyAv in self.__avatarControllers:
            if userId == pyAv.userId_:
                return pyAv

        return

    def setUndoUserInterfaceController(self, undoUIController):
        self.__roomController.setUndoUserInterfaceController(undoUIController)
        return

    def setUndoAndRedoHistoryFlags(self, slotId, hasUndoHistory, hasRedoHistory):
        self.__scenePresenter.setUndoAndRedoHistoryFlags(slotId, hasUndoHistory, hasRedoHistory)
        return

    def flashIndicatorIfLockStateChange(self, slotId, furniStateBefore, furniStateAfter):
        self.__scenePresenter.flashIndicatorIfLockStateChange(slotId, furniStateBefore, furniStateAfter)
        return

    def loadActionAndEffects(self, desiredActionName, productId, modelDefinition, userId, isAvatar, avatarProductId):
        return self.__scenePresenter.loadActionAndEffects(desiredActionName, productId, modelDefinition, userId, isAvatar, avatarProductId)

    @task
    def __loadAndTriggerAvatarActions(self, pitcherActionName, pitcherActionUrl, pitcherUserId, catcherActionName, catcherActionUrl, catcherUserId):
        logger.info('__loadAndTriggerAvatarActions(): %r %r %r %r %r %r', pitcherActionName, pitcherActionUrl, pitcherUserId, catcherActionName, catcherActionUrl, catcherUserId)
        pitcherAv = self.pyAvForUserId(pitcherUserId)
        if pitcherAv is None:
            return
        else:
            pitcherPid = product.getPidFromProductUrl(pitcherActionUrl)
            if not catcherUserId:
                pitcherAv.triggerActionByPid(pitcherPid, pitcherActionName)
            else:
                catcherAv = self.pyAvForUserId(catcherUserId)
                if catcherAv is None:
                    return
                catcherPid = product.getPidFromProductUrl(catcherActionUrl)
                pitcherAv.triggerTwoPartyAction(catcherAv, pitcherPid, pitcherActionName, catcherPid, catcherActionName)
            return

    def handleClickOnAvatar(self, pos, userId):
        self.__serviceProvider.eventBus.fire(self, 'ClickedOnAvatar', {'pos': pos, 'userId': userId})
        return

    def onDraggedCamera(self, distance):
        self.__serviceProvider.eventBus.fire(self, 'DraggedCamera', {})
        if distance > 8:
            self.__onMoveCamera()
        return

    def onMouseClick(self):
        if self.__modeManager.getActiveMode():
            if not self.__modeManager.getActiveMode().activeTool or self.__modeManager.getActiveMode().activeTool.canLoseFocus():
                self.setFocus3DWindow('AvatarWindowNotificationMouseButtonClick')
        return

    @task
    def __sendDrv(self, key, value):
        yield imvu.http.securePost(url='https://' + self.__serviceProvider.network.getSecureDomain() + '/api/drv.php', params={'name': key, 'value': value}, auth=self.__userAccount.getAuth(), responseSchema=[], network=self.__serviceProvider.network)
        return

    def onAvatarSeatChanged(self, sceneObject, oldSeatIndex, oldFurniInstanceId, seatIndex, furniInstanceId):
        logger.info('SessionWindow.onAvatarSeatChanged(%r, %r, %r, %r, %r)', sceneObject, oldSeatIndex, oldFurniInstanceId, seatIndex, furniInstanceId)
        self.__serviceProvider.eventBus.fire(self, 'AvatarSeatChanged', dict(userId=sceneObject.getUserId(), oldSeatIndex=oldSeatIndex, seatIndex=seatIndex, furniInstanceId=furniInstanceId))
        if self.__pilotUserId == sceneObject.getUserId():
            self.__onMySeatChanged(oldSeatIndex, oldFurniInstanceId, seatIndex, furniInstanceId)
        self.__scenePresenter.onAvatarSeatChanged(sceneObject, oldSeatIndex, oldFurniInstanceId, seatIndex, furniInstanceId)
        if seatIndex == 0:
            import traceback
            stack_buf = traceback.format_stack()
            logger.warning('SessionWindow.onAvatarSeatChanged (seatIndex=0) (%r, %r, %r, %r, %r)', sceneObject, oldSeatIndex, oldFurniInstanceId, seatIndex, furniInstanceId)
            drv_buf = '(%r, %r, %r, %r, %r, %r)' % (sceneObject, oldSeatIndex, oldFurniInstanceId, seatIndex, furniInstanceId, stack_buf)
            self.attachTask(self.__sendDrv('client.drv.invalid_seat_index', drv_buf))
        return

    def sendMessageToAll(self, message, idparta, idpartb, p1, p2):
        controlMessage = '*msg %s %d %d %d %d' % (message, idparta, idpartb, p1, p2)
        self.notifyChatMessage(controlMessage)
        return

    @property
    def avatars(self):
        return list(self.__avatarControllers)

    def getLoadingProductIds(self):
        rv = set()
        for avatar in self.avatars:
            rv |= avatar.loadingPids

        return rv

    @task
    def removeProductById(self, productId, pyAv):
        logger.info('removeProductById: productId %s, pyAv %s', productId, pyAv)
        if pyAv == self.myAvatar:
            self.__cancelOutfitPhoto()
        numRemoved = 0
        numRemoved += pyAv.removePids([productId])
        if pyAv.userId == self.__roomController.ownerId:
            numRemoved += (yield self.__roomController.removePids([productId]))
        if not numRemoved:
            raise ValueError()
        return

    def __checkUseProductPolicy(self, pi, controllerToApplyTo):
        if not self.__useProductPolicy:
            return True
        return self.__useProductPolicy(pi, controllerToApplyTo)

    def isLockedRoom(self):
        debug = self.__roomController.isLockedRoomBodyPattern()
        return self.__roomController.isLockedRoomBodyPattern() and not self.__scenePresenter.roomHasFurnitureNodes()

    def __canUseFurnitureProduct(self, pyAv):
        if pyAv.userId == self.__pilotUserId:
            if not self.isRoomOwner(pyAv.userId):
                logger.info('__canUseFurnitureProduct(): False, not room owner')
                self.messageShow(self.__serviceProvider.translationTable.LS('Only the owner of a room can add furniture to it'), 2700)
                return False
            if self.isLockedRoom():
                logger.info('__canUseFurnitureProduct(): False, locked room')
                self.messageShow(*CannotAddFurnitureToLockedRoomMessage)
                return False
        elif not self.isRoomOwner(pyAv.userId):
            logger.info('ignoring useLoadedProduct furni request because session_window roomOwner != pyAv %r', pyAv)
            return False
        return True

    @task
    def __canChangePublicRoomToProduct(self, product):
        productId = product.getProductId()
        session = self.__session
        logger.info('Checking applied product against room state product: %s', productId)
        canChangeRoom = True
        session_roomInstanceId = session.getRoomInstanceId()
        try:
            session_roomState = yield self.__userAccount.getRoomStateEx(session_roomInstanceId, None)
            session_roomPid = int(session_roomState['room_state']['room_info']['room_pid'])
        except Exception as e:
            logger.exception('Error in getRoomState(), using fallback pid')
            session_roomPid = WHITE_ROOM_PRODUCT_ID

        if self.__roomController.roomState:
            cur_roomInstanceId = yield self.__roomController.roomState.getInstanceId()
            if cur_roomInstanceId and cur_roomInstanceId == session_roomInstanceId:
                canChangeRoom = False
        if session_roomPid != productId:
            canChangeRoom = False
        if self.__roomController.roomState:
            roomProductId = yield self.__roomController.roomState.getRoomProductId()
            if roomProductId == self.__errorRoomPid:
                logger.info('Overriding current room pid because it is the error room pid')
                canChangeRoom = True
        if productId == self.__errorRoomPid:
            logger.info('Applying error room pid')
            canChangeRoom = True
        logger.info('canChangeRoom = %s', canChangeRoom)
        yield Return(canChangeRoom)
        return

    def useLoadedProduct(self, product, pyAv):
        if not self.__checkUseProductPolicy(product, pyAv):
            return
        try:
            pyAv.applyProduct(product)
        except imvu.scene.IncompatibleBodyException:
            self.__unhandledAvatarProduct(pyAv, product, True)
        except imvu.scene.SceneStateException:
            self.__unhandledAvatarProduct(pyAv, product, False)

        return

    def __updateNameTags(self):
        for pyAv in self.__avatarControllers:
            self.__updateNameTag(pyAv=pyAv)

        return

    def __updateNameTag(self, pyAv):
        avDownloadSize = self.getAvatarDownloadSize(pyAv)
        avKb = self.__formatNumber(avDownloadSize / 1000.0)
        pyAv.setBubbleStreamInfoTag('%sKB' % avKb)
        if not pyAv.nameTagColor:
            if pyAv.userId == self.__pilotUserId:
                pyAv.nameTagColor = SELF_AVATAR_COLOR
            else:
                count = len(OTHER_AVATAR_COLORS)
                idx = self.__avatarColorIndex % count
                pyAv.nameTagColor = OTHER_AVATAR_COLORS[idx]
                self.__avatarColorIndex += 1
        return

    def getAvatarDownloadSize(self, pyAv):
        sizes = {}
        for p in pyAv.allProductsWorn():
            sizes.update(p.getMinimumDownloadSizes())

        return sum(sizes.values())

    def getSceneMetrics(self):
        room = self.sceneViewer.getRoomMetrics()
        room['minimumDownloadSize'] = self.getProductsDownloadSize(self.__scenePresenter.getProductsInUse())

        def calculateMetrics(avatar):
            metrics = self.sceneViewer.getAvatarMetrics(avatar.getSceneObject())
            metrics['minimumDownloadSize'] = self.getProductsDownloadSize(avatar.productsInUse)
            return metrics

        return {'room': room, 
           'avatars': (dict((avatar.avatarName, calculateMetrics(avatar)) for avatar in self.avatars))}

    def __formatNumber(self, num):
        sl = [c for c in str(int(num))]
        for i in range(len(sl) - 3, 0, -3):
            sl[i:i] = [',']

        return ('').join(sl)

    def notifyProductChanges(self, event):
        pyAv = event.sender
        self.__updateNameTag(pyAv)
        products = pyAv.stateAsProducts()
        productIds = [product.getProductId() for product in products]
        self.__serviceProvider.eventBus.fire(self, 'AvatarClothingChanged', {'userId': (pyAv.userId_), 'products': products, 'productIds': productIds})
        if self.shouldSaveAvatarProductChange(pyAv):

            @task
            def doit():
                yield Sleep(2)
                try:
                    self.__userAccount.saveOutfit(pyAv.stateAsPids())
                except Exception:
                    logger.exception('non-fatal error: Failed to write avatar config')

                return

            self.attachTask(doit())
        if pyAv.userId == self.__pilotUserId:
            self.__serviceProvider.eventBus.fire(self, 'SessionWindow.avatarClothingUpdated')
        return

    def __handleRoomAuthError(self):
        duration = 9000
        if self.__session.isRoomSession():
            message = 'Sorry, we are experiencing problems loading\n\nthis room at this time. Please try again later.'
        elif self.isRoomOwner():
            message = 'We are experiencing a problem loading your\n\nroom.  Please check your default room setting.'
        else:
            message = 'We are experiencing a problem loading this\n\nroom.  Please try visiting a different room.'
        self.__displayCenteredFafMessage(duration, 'Problem Loading Room', message, closeable=True)
        return

    def __roomStateChanged(self, event):
        if event.info['reason'] != 'bringStateCurrent':
            self.broadcastMyState('__roomStateChanged')
        return

    def shouldSaveAvatarProductChange(self, pyAv):
        return self.canModifyDefaultOutfit and pyAv.userId_ == self.__pilotUserId and pyAv.getBodyPattern()

    def __status(self):
        return 'SessionWindow 0x%x status: dirty %s, %d avatars' % (
         hash(self),
         False,
         len(self.__avatarControllers))

    def getPilotAvatar(self):
        for pyAv in self.__avatarControllers:
            if pyAv.userId_ == self.__pilotUserId:
                return pyAv

        return

    def getNonPilotAvatars(self):
        return [pyAv for pyAv in self.__avatarControllers if pyAv.userId_ and pyAv.userId_ != self.__pilotUserId]

    __notifiedOfConversation = False

    def __considerSendingServerNotify(self):
        otherUserIds = [av.userId for av in self.getNonPilotAvatars()]
        if not otherUserIds:
            return
        if self.__notifiedOfConversation:
            return
        self.__notifiedOfConversation = True
        otherAvUserId = otherUserIds[0]

        @task
        def notify():
            try:
                yield self.__userAccount.notifyServerConversation2(otherAvUserId)
            except xmlrpclib.Fault as error:
                if error.faultCode == imvu.gateway.ERROR_INVALID_AUTH_DATA and not imvu.config.IgnoreLoginCollisions:
                    raise LoginCollisionException()
                logger.exception('fault while notifying of conversation')
            except networkExceptions as error:
                logger.exception('considerSendingServerNotify error type %s, %r', type(error), error)
                self.__notifiedOfConversation = False

            return

        self.attachTask(notify())
        self.__userAccount.recordFact('Chat %s 60s' % self.__chatMode, {})
        return

    def __stepLoadingProductsMessage(self):
        if self.isFullyLoaded():
            return
        msg_info = {'dialogText': ''}
        msg_info['duration'] = 1.5
        msg_info['dialogText'] = '{CloseBox}1{/CloseBox}'
        msg_info['dialogText'] += '{WindowHeight}60{/WindowHeight}'
        msg_info['dialogText'] += '{PointSize}16{/PointSize}'
        msg_info['dialogText'] += '{Timeout}9000{/Timeout}'
        msg_info['dialogText'] += '\n\n' + self.__serviceProvider.translationTable.LS('Loading products')
        self.__fafManager_.setFafMessageInfo('loading_products', msg_info)
        return

    def __getWhatsDirty(self):
        return self.__roomController.dirty() or self.__roomController.isFurniDirty() or any(pyAv.dirty() for pyAv in self.__avatarControllers)

    def messageShow(self, messageText, numSteps):
        if isinstance(messageText, LString) or isinstance(messageText, FLString):
            messageStr = messageText.translateString(self.__serviceProvider.translationTable)
        else:
            messageStr = messageText
        logger.info('Showing message %r', messageStr)
        unicode(messageStr)
        if not self.isDisposed():
            id = self.__sceneWindow.avatarWindow.newFireAndForgetMessage(messageStr, numSteps)
            return id
        return

    def messageClose(self, id):
        if id is not None:
            self.__sceneWindow.avatarWindow.setFireAndForgetMessageOff(id)
        return

    def messageReplaceText(self, messageId, newText):
        if type(newText) is not unicode:
            newText = unicode(newText, getStringEncoding())
        self.__sceneWindow.avatarWindow.replaceFireAndForgetMessageText(messageId, newText)
        return

    def messageUpdateHeight(self, messageId, height):
        self.__sceneWindow.avatarWindow.setFireAndForgetHeightValue(messageId, height)
        return

    def __getRoomPidFromExportedRoomState(self, exportedState):
        try:
            roomPid = int(exportedState['room_state']['room_info']['room_pid'])
        except Exception:
            roomPid = None

        return roomPid

    def __resetRoomFromDefinition(self):
        logger.info('__resetRoomFromDefinition')
        assertInRelease(self.__roomController)
        session = self.__session
        if session.isRoomSession() and not self.__forcedRoomState:
            self.__resetPublicRoomFromDefinition()
        else:
            roomPid = self.__getRoomPidFromExportedRoomState(self.__forcedRoomState) or self.__forcedRoom or self.__userAccount.getDefaultRoom() or WHITE_ROOM_PRODUCT_ID
            self.attachTask(self.__loadRoom(roomPid=roomPid, roomOwner=self.__pilotUserId))
        return

    resetRoomFromDefinition = __resetRoomFromDefinition

    @task
    def __loadRoom(self, roomOwner=None, roomPid=None, roomState=None, pi=None, trialAuth=False):
        if roomState:
            if roomPid is None:
                roomPid = yield roomState.getRoomProductId()
            if roomOwner is None:
                roomOwner = yield roomState.getUserId()
        if pi is None:
            userIds = self.__session.getRoomOwners()
            if roomOwner not in self.__session.getRoomOwners():
                userIds = [
                 roomOwner] + userIds
            for userId in userIds:
                while True:
                    try:
                        pi = yield self.__productLoader.createProductInstance(userId, roomPid, trialAuth=trialAuth)
                        break
                    except product.ProductAuthorizationError as e:
                        logger.exception('error loading room product: %r', e)
                        break
                    except product.ProductLoadError as e:
                        logger.exception('failed to load room product: %r', e)
                        if not e.isTransient:
                            raise
                        yield Sleep(10)

                if pi is not None:
                    break

            if pi is None:
                self.__handleRoomAuthError()
                return
        if roomState is None:
            if roomPid is None:
                roomPid = pi.getProductId()
            if self.__getRoomPidFromExportedRoomState(self.__forcedRoomState) == roomPid:
                roomState = self.__serviceProvider.roomStateManager.createLocalRoomState(localState=self.__forcedRoomState)
            elif self.__roomStateIsLocal:
                roomState = self.__serviceProvider.roomStateManager.createLocalRoomStateFromServer(roomPid)
            elif roomOwner != self.__pilotUserId:
                roomState = self.__serviceProvider.roomStateManager.createLocalRoomState(self.__serviceProvider.roomStateManager.makeEmptyExportedStateForProductId(self.__userAccount.getUserId(), roomPid))
            else:
                roomState = self.__serviceProvider.roomStateManager.createRoomStateForProductId(roomPid)
        yield self.__roomController.loadRoomState(roomState, pi)
        self.sceneViewer.clearHotspotIndicatorHudObject()
        self.__serviceProvider.eventBus.fire(self, 'SessionWindow.roomUpdated')
        return

    def __isIncomingChatSession(self):
        return isinstance(self.__session, im.meet.ChatSession) or isinstance(self.__session, ChangeableSession) and isinstance(self.__session.innerSession, im.meet.ChatSession)

    @activemethod
    def __resetPublicRoomFromDefinition(self, roomOwner=None):
        instanceId = self.__session.getRoomInstanceId()
        roomState = self.__serviceProvider.roomStateManager.createRoomStateForInstanceId(instanceId, canBeModified=self.__session.isOwner(self.__userAccount.getUserId()))
        if (yield roomState.loadFailed()):
            logger.exception('Error in getRoomState() defaulting to white room')
            self.__errorRoomPid = WHITE_ROOM_PRODUCT_ID
            self.messageShow(*CouldNotGetRoomStateMessage)
            roomState = self.__serviceProvider.roomStateManager.createLocalRoomState(self.__serviceProvider.roomStateManager.makeEmptyExportedStateForProductId(self.__userAccount.getUserId(), self.__errorRoomPid))
        yield self.__loadRoom(roomState=roomState, roomOwner=roomOwner or self.__session.getOwner())
        return

    def onActivate(self):
        self.setFocus3DWindow('onActivate sessionwindow')
        return

    def onDeactivate(self):
        return

    def onChangeEnabled(self, enabled):
        if self.__sceneWindow:
            self.__sceneWindow.onChangeEnabled(enabled)
        return

    def setSeat(self, pyAv, seat):
        logger.info('setSeat(): pyAv: %r seat: %r', pyAv, seat)
        try:
            seatNumber, furniInstanceId = seat
            seatNumber = int(seatNumber)
            if not isinstance(seatNumber, int):
                raise Exception('invalid seat number')
        except Exception:
            logger.exception('setSeat failed to parse seat number, bailing out')
            return

        if pyAv.avatarModel.seat == seat:
            return
        else:
            oldAv = None
            for av in self.__avatarControllers:
                if av.avatarModel.seat == seat:
                    if av != pyAv:
                        assertInRelease(not oldAv, 'more than one avatar in seat %r' % (seat,))
                        oldAv = av

            if oldAv:
                oldAv.avatarModel.setSeat(pyAv.avatarModel.seat)
            pyAv.avatarModel.setSeat(seat)
            return

    @property
    def roomController(self):
        return self.__roomController

    @property
    def myAvatar(self):
        assertInRelease(self.__avatarControllers, 'SessionWindow has no avatars')
        for pyAv in self.__avatarControllers:
            if pyAv.userId == self.__pilotUserId:
                return pyAv
        else:
            assertInRelease(False, 'Could not find myAvatar for userId_ %s in __avatars array %s' % (self.__pilotUserId, self.__avatarControllers))

        return

    def myAvatarBodyPatternId(self):
        if not self.__avatarControllers:
            return None
        else:
            pyAv = self.myAvatar
            if not pyAv.getBodyPattern():
                return None
            return pyAv.getBodyPattern().getProductId()

    def isDisposed(self):
        return self.__disposed

    def dispose(self):
        logger.info('SessionWindow.dispose(), changeableSession: %r', self.__session.innerSession)
        self.__disposed = True
        if self.__sceneWindow is None:
            return
        else:
            FlashUrlLoader.unregisterUrlHandler(self.__handleFlashUrlRequest)
            self.__session.closeSession()
            self.stopAttachedTasks()
            self.stopEvents()
            self.__seatAssignmentTasks.clearTasks()
            self.__animationTasks.clearTasks()
            for pyAv in self.__avatarControllers:
                pyAv.stopAttachedTasks()

            self.__sceneWindow.avatarWindow.setAvatarWindowUser(None)
            self.__clearFlashOverlays()
            self.__widgetSpace = None
            self.__roomController.dispose()
            logger.info('Reparenting avatarWindow')
            self.__sceneWindow.avatarWindow.setVisible(False)
            self.__sceneWindow.avatarWindow.unsetParentWindow()
            del self.__avatarControllers[:]
            logger.info('Destroying avatarWindow')
            self.__scenePresenter.dispose()
            self.__scenePresenter = None
            self.__sceneWindow.dispose()
            self.__sceneWindow = None
            logger.info('AvatarWindow destroyed')
            self.__roomController = None
            self.__parentInputEventHandler = None
            self.__awayPresenter.dispose()
            self.__serviceProvider.eventBus.fire(self, 'Closed')
            if self.__photoWidget:
                self.__photoWidget.dispose()
            return

    def removeAvatar(self, pyAv):
        assertInRelease(pyAv)
        logger.info('Removing avatar %s', pyAv)
        if pyAv in self.__avatarControllers:
            pyAv.stopAttachedTasks()
            self.__avatarControllers.remove(pyAv)
        self.__sceneModel.removeAvatarModel(pyAv.avatarModel)
        return

    def getPhotoWidget(self):
        return self.__photoWidget

    def takePhoto(self, viewport='Portrait', photoWidgetFactory=None, mode=None, photoReviewFactory=None, themeId=None, themeName=None, roomName=None):
        assertInRelease(photoWidgetFactory is not None)
        assertInRelease(photoReviewFactory is not None)

        @task
        def take():
            yield self.__createPhotoWidget(photoWidgetFactory)
            if self.__notSavingPhoto.isSet():
                self.__notSavingPhoto.clear()
            photo = yield self.__photoWidget.take(viewport)
            if photo:
                varName = ''
                if photo['photoType'] == 'portrait':
                    varName = 'PhotoUploadReplaceProfilePic'
                elif photo['photoType'] == 'landscape':
                    varName = 'PhotoUploadReplaceRoomPic'
                replacePhoto = self.__serviceProvider.localStore.getForUser(self.__userAccount.getUserId(), varName, True)
                allowShare = self.__userAccount.shouldSeeSharePhotos()
                shareDefault = self.__serviceProvider.localStore.getForUser(self.__userAccount.getUserId(), 'PhotoUploadShareDefault', False)
                hasUnpublishedPids = isinstance(mode, imvu.mode.ProductEditMode) or (yield self.hasUnpublishedProductsInScene())
                hasAPPids = yield self.hasAPProductsInScene()
                hasAPPlusPids = yield self.hasAPPlusProductsInScene()
                disclaimer = ''
                if hasAPPids or hasUnpublishedPids or hasAPPlusPids:
                    allowShare = False
                    if hasAPPlusPids and hasUnpublishedPids:
                        disclaimer = self.__serviceProvider.translationTable.LS('Scenes containing AP+ products and unpublished products cannot be shared.')
                    elif hasAPPids and hasUnpublishedPids:
                        disclaimer = self.__serviceProvider.translationTable.LS('Scenes containing AP products and unpublished products cannot be shared.')
                    if hasAPPlusPids:
                        disclaimer = self.__serviceProvider.translationTable.LS('Scenes containing AP+ products cannot be shared.')
                    elif hasAPPids:
                        disclaimer = self.__serviceProvider.translationTable.LS('Scenes containing AP products cannot be shared.')
                    elif hasUnpublishedPids:
                        disclaimer = self.__serviceProvider.translationTable.LS('Scenes containing unpublished products cannot be shared.')
                result = self.__serviceProvider.dialogManager.showModal(self.window, photoReviewFactory({'path': (photo['path']), 'photoType': (photo['photoType']), 'replacePhoto': replacePhoto, 'allowShare': allowShare, 'shareDefault': shareDefault, 'disclaimer': disclaimer, 'roomName': roomName, 'theme_name': themeName}))
                if varName != '':
                    self.__serviceProvider.localStore.setForUser(self.__userAccount.getUserId(), varName, result['replace_photo'])
                if allowShare:
                    self.__serviceProvider.localStore.setForUser(self.__userAccount.getUserId(), 'PhotoUploadShareDefault', result['share_photo'])
                if result and result['upload']:
                    yield self.__uploadPhoto(image=photo['imageData'], action=result['action'], sharePhoto=result['share_photo'], themeId=themeId, roomName=roomName)
                    self.__notSavingPhoto.set()
                elif result and result['take_again']:
                    self.takePhoto(viewport=viewport, photoWidgetFactory=photoWidgetFactory, mode=mode, photoReviewFactory=photoReviewFactory, themeId=themeId, roomName=roomName, themeName=themeName)
                else:
                    self.__notSavingPhoto.set()
            else:
                self.__notSavingPhoto.set()
            return

        self.attachTask(take())
        return

    def changeOutfitPhoto(self, outfitInfo, photoWidgetFactory):

        @task
        def takeOutfitPhoto():
            yield self.__createPhotoWidget(photoWidgetFactory)
            self.myAvatar.setOutfit(self.__getCurrentPidsFromOutfitInfo(outfitInfo))
            self.__outfitInfoForPictureChange = outfitInfo
            photo = yield self.__photoWidget.take(viewport='Outfit')
            if photo:
                self.__userAccount.recordFact('Take Custom Outfit Snapshot', {})
                imvu.dialog.outfitcard.showOutfitCard(self.window, self.__serviceProvider, outfitInfo, self, self.__userAccount, photo['path'], photo['imageData'])
            return

        self.attachTask(takeOutfitPhoto())
        return

    def __showPhotoUploadError(self):
        self.__serviceProvider.dialogManager.showModal(self.window, imvu.dialog.AlertDialog(self.__serviceProvider.translationTable.LS('Upload Error'), self.__serviceProvider.translationTable.LS('There was an error uploading your photo.  Please try again.')))
        return

    def __showThemedRoomUploadError(self):
        self.__serviceProvider.dialogManager.showModal(self.window, imvu.dialog.ThemedRoomUploadFailureDialog())
        return

    @task
    def __handleThemeRoomStatusChange(self):
        try:
            roomInfo = yield self.__serviceProvider.clientGateway.getRoomCardInfo(self.__roomController.roomInstanceId)
        except networkExceptions:
            logger.exception("couldn't get info for room instance id %r", self.__roomController.roomInstanceId)
            return

        self.__serviceProvider.eventBus.fire(self, 'ThemedRoomStatusChanged', roomInfo)
        return

    @task
    def __handleThemedRoomInEligibleError(self):
        self.attachTask(self.__handleThemeRoomStatusChange())
        self.__showThemedRoomUploadError()
        return

    @task
    def __handleThemedRoomSubmissionSuccess(self, roomName):
        if roomName and len(roomName) > 33:
            roomName = roomName[:30] + '...'
        self.attachTask(self.__handleThemeRoomStatusChange())
        self.__serviceProvider.dialogManager.showModal(self.window, imvu.dialog.ConfirmationDialog(self.__serviceProvider.translationTable.LS('Submission Success'), self.__serviceProvider.translationTable.FLS("Thanks for submitting {roomName} to Featured Rooms. We'll be in touch if your Chat Room gets selected.", roomName=roomName)))
        return

    @task
    def __uploadPhoto(self, image, action, sharePhoto=False, themeId=None, roomName=None):
        factUploadTo = 'gallery'
        if action == 'room':
            factUploadTo = 'roomPic'
        elif action == 'avatar':
            factUploadTo = 'avatarPic'
        self.__userAccount.recordFact('Take a Snapshot', {'upLoadTo': factUploadTo})
        pids = {}
        if sharePhoto:
            pids = self.getProductsInScene()
        themedRoomData = {}
        if action == 'themed_room':
            themedRoomData = {'room_instance_id': (self.__session.getRoomInstanceId()), 'theme_id': themeId}
        try:
            uploadResult = yield self.__userAccount.uploadImageToProfile(self.__serviceProvider, image=image, source='camera', action=action, sharePhoto=sharePhoto, pidsInScene=pids, themedRoomData=themedRoomData, room_id=self.__session.getRoomInstanceId() if sharePhoto and self.__session.getRoomInstanceId else None)
            if uploadResult['result'] != 'success':
                self.__showPhotoUploadError()
        except NetworkSchemaError:
            if themeId:
                self.attachTask(self.__handleThemedRoomInEligibleError())
            else:
                self.__showPhotoUploadError()
        except networkExceptions:
            if themeId:
                self.__showThemedRoomUploadError()
            else:
                self.__showPhotoUploadError()

        if themeId is not None:
            self.attachTask(self.__handleThemedRoomSubmissionSuccess(roomName))
        if action == 'avatar':
            imageUrl = imvu.network.getUserImagesDomain() + uploadResult['new_mogile_key']
            self.__serviceProvider.eventBus.fire(self, 'AvPicChanged', {'url': imageUrl})
        return

    @task
    def __createPhotoWidget(self, photoWidgetFactory):
        if self.__photoWidget is None:
            self.__photoWidget = yield self.__serviceProvider.create(photoWidgetFactory, sessionWindow=self, userAccount=self.__userAccount)
            self.addHtmlOverlay(self.__photoWidget)
        return

    def __getCurrentPidsFromOutfitInfo(self, info):
        return set(self.__parsePidsStr(info['pids'])) - set(info.get('removePids', []))

    def __addFlashOverlay(self, url, listenerFactory=FlashCallHandler, zindex=0):
        logger.info('SessionWindow.addFlashOverlay(): url: %r listenerFactory: %r', url, listenerFactory)
        if not self.sceneViewer:
            return
        listener = self.__serviceProvider.create(listenerFactory, sessionWindow=self)

        def addFlashOverlay(listener):
            window = self.sceneViewer.getRenderedWindow()
            frc = self.__serviceProvider.flashOverlayFactory(window.hwnd, listener)
            self.sceneViewer.addFlashOverlay(frc)
            return frc

        context = FlashContext(self.__serviceProvider, addFlashOverlay, listener)
        context.play(url)
        self.__flashRenderContexts.append(context)
        self.sceneViewer.setFlashOverlayZIndex(context.renderer, zindex)
        logger.debug('Successfully added FlashRenderContext(%r) to SessionWindow' % url)
        return context

    def __clearFlashOverlays(self):
        logger.info('__clearFlashOverlays')
        self.sceneViewer.clearFlashOverlays()
        for frc in self.__flashRenderContexts:
            if hasattr(frc, 'dispose'):
                logger.info('Disposing %r', frc)
                frc.dispose()

        del self.__flashRenderContexts[:]
        return

    def __onMoveCamera(self):
        self.__userAccount.recordFactOnlyOnce('Move Camera', {})
        return

    def __onMySeatChanged(self, oldSeatIndex, oldFurnitureInstanceId, seatIndex, furniInstanceId):
        if (oldSeatIndex, oldFurnitureInstanceId) == (seatIndex, furniInstanceId):
            return
        else:
            self.__recordChangeSeatFact(seatIndex, furniInstanceId)
            self.myAvatar.avatarModel.setSeat((seatIndex, furniInstanceId))
            self.__session.sendImMessage('*msg SeatAssignment 2 %i %i %i' % (self.__pilotUserId, seatIndex, furniInstanceId))
            self.updateChatSeat(seatIndex, furniInstanceId)
            if oldFurnitureInstanceId != furniInstanceId:
                oldFurniProduct = newFurniProduct = None
                oldSlotId = self.__scenePresenter.getSlotIdForFurnitureId(oldFurnitureInstanceId)
                if oldSlotId:
                    oldFurniProduct = self.__roomController.getFurnitureProduct(oldSlotId)
                newSlotId = self.__scenePresenter.getSlotIdForFurnitureId(furniInstanceId)
                if newSlotId:
                    newFurniProduct = self.__roomController.getFurnitureProduct(newSlotId)
                if self.__serviceProvider.prefService.getPref('enableFlashWidgets'):
                    self.__widgetSpace.onLocalSeatChanged(oldFurniProduct, newFurniProduct)
                if newFurniProduct:
                    webLinkKey = newFurniProduct.productProperty('WebRedirectKey', False)
                    if self.__roomController.roomInstanceId:
                        rid = self.__roomController.roomInstanceId
                    else:
                        rid = 'none'
                    if webLinkKey:
                        self.__serviceProvider.browser.launchNamedUrl('productRedirect', {'target': webLinkKey, 'pid': (newFurniProduct.getProductId()), 'rid': rid})
            return

    def setNumBubblesVisible(self, num):
        if self.__sceneWindow:
            self.__sceneWindow.avatarWindow.setNumBubblesVisible(int(num))
        return

    def setFocus3DWindow(self, reason='unknown'):
        if self.__sceneWindow:
            logger.info('setFocus3DWindow(), 0x%x, reason: %s' % (self.__sceneWindow.avatarWindow.getRenderedWindow().hwnd, reason))
            self.__sceneWindow.avatarWindow.setFocus3DWindow()
        mode = self.__modeManager.getActiveMode()
        if mode is not None:
            mode.setFocus3DWindow()
        return

    def rotateBubblesVisible(self):
        self.__sceneWindow.avatarWindow.rotateBubblesVisible()
        return

    @property
    def __pilotUserId(self):
        return self.__userAccount.getUserId()

    def getNonPilotUserIdList(self):
        return [av.userId for av in self.getNonPilotAvatars()]

    def isTakingPhoto(self):
        return self.__photoWidget and self.__photoWidget.isTakingPhoto()

    @task
    def waitIfTakingPhoto(self):
        if self.isTakingPhoto():
            yield self.__photoWidget.waitForTakingPhoto()
        yield self.__notSavingPhoto.wait()
        return

    @property
    def inputEventHandler(self):
        return self.__inputEventHandler

    def onKeyEventDown(self, WM_CHAR_wParam, modifierControl, modifierShift):
        return self.__inputEventHandler.onAvatarWindowKeyEventDown(WM_CHAR_wParam, modifierControl, modifierShift)

    def onKeyEventUp(self, WM_CHAR_wParam, modifierControl, modifierShift):
        return self.__inputEventHandler.onAvatarWindowKeyEventUp(WM_CHAR_wParam, modifierControl, modifierShift)

    def handleUiEvent(self, event):
        evt = inputevent.translateUiEvent(event)
        if evt is not None and self.__parentInputEventHandler is not None:
            self.__parentInputEventHandler.handleInputEvent(self, evt)
        return

    def getParentInputEventHandler(self):
        return self.__parentInputEventHandler

    def handleInputEvent(self, sender, inputEvent):
        if inputEvent.eventType == 'keydown':
            return self.__inputEventHandler.onKeyEventDown(sender, keyCode=inputEvent.keyCode, ctrlKey=inputEvent.ctrlKey, shiftKey=inputEvent.shiftKey)
        else:
            if inputEvent.eventType == 'DOMMouseScroll':
                return self.__inputEventHandler.onMouseWheelScroll(sender, delta=inputEvent.delta, screenX=inputEvent.screenX, screenY=inputEvent.screenY)
            return False

        return

    def __legacyOutfitUpdate(self, updates, outfit):
        copy = updates.copy()
        if outfit:
            copy.update({'legacy_outfit_message': ('*use %s' % (' ').join(map(str, outfit)))})
        return copy

    def updateChatOutfit(self):
        try:
            pyAv = self.myAvatar
        except Exception:
            return

        outfit = list(pyAv.stateAsPids())
        outfit.extend(pyAv.loadingPids)
        if set(outfit) != set(self.__lastOutfit):
            self.__lastOutfit = outfit
            self.__session.updateParticipantInfo(self.__userAccount, self.__legacyOutfitUpdate({}, self.__lastOutfit))
        return

    def __chatSeatUpdate(self, updates, seatNumber, furniInstanceId):
        copy = updates.copy()
        copy.update({'seat_number': seatNumber, 
           'seat_furni_id': furniInstanceId})
        return copy

    def updateChatSeat(self, seatNumber, furniInstanceId):
        self.__session.updateParticipantInfo(self.__userAccount, self.__chatSeatUpdate({}, seatNumber, furniInstanceId))
        return

    def __imqConnected(self, event):
        seat = self.myAvatar.avatarModel.seat
        updates = self.__legacyOutfitUpdate(self.__chatSeatUpdate({}, seat[0], seat[1]), self.__lastOutfit)
        if updates:
            self.__session.updateParticipantInfo(self.__userAccount, updates, force=True)
