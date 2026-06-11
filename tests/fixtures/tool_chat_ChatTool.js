function ChatTool(imvu, eventBus, textChatElement, network) {
    this.imvu = imvu;
    this.network = network;
    this.eventBus = eventBus;
    this.eventBus.clearScope('ChatTool');
    this.textChatElement = textChatElement;
    this.historyElement = textChatElement.querySelector('#history');
    this.sendButtonElement = textChatElement.querySelector('#send-button');
    this.inputElement = textChatElement.querySelector('input');
    this.textBubbleActive = false;
    this.chatParticipants = {};
    this.hideElement = textChatElement.querySelector('#hideChat');
    this.ctaElement = textChatElement.querySelector('.chat-cta');
    this.showElement = textChatElement.querySelector('#showChat');
    this.inputRowElement = textChatElement.querySelector('#inputRow');
    this.header = textChatElement.querySelector('#header');
    this.textSizeElement = textChatElement.querySelector('#textSize');
    this.closeButtonElement = textChatElement.querySelector('#closebutton');
    this.opacityFactor = 0.5;
    this.largeText = false;
    this.pendedTryProductMessages = {};
    this.whisperers = [];

    this.newWhisperIndicator = textChatElement.querySelector('#new-whisper-indicator');
    this.elementToScrollTo = null;

    this.allowShopping = this.imvu.call('allowShopping');
    this.allowClose = this.imvu.call('allowClose');

    this.FULL_WIDTH = 404;
    this.FULL_HEIGHT = 237;

    this.localUserId = this.imvu.call('getCustomerId');
    this.whisperTargetId = 0;
    this.whisperTargetName = '';

    $(this.textChatElement.querySelector('#new-whisper-indicator .stop')).click(this.cancelWhisper.bind(this));
    $(this.textChatElement.querySelector('.whisper-indicator')).click(this.cancelWhisper.bind(this));

    $(this.textChatElement.querySelector('#invert')).click(this.invert.bind(this));

    $(this.sendButtonElement).click(this.onSubmit.bind(this));
    $(this.inputElement).keypress(function(e) { 
        if(e.keyCode === 13) { 
            this.onSubmit();
        }
    }.bind(this));
    IMVU.Client.util.hint([this.inputElement]);
    YAHOO.util.Event.addListener(this.historyElement, 'contextmenu', this.onHistoryContextMenu, this, true);
    YAHOO.util.Event.addListener(this.inputElement, 'contextmenu', this.onInputContextMenu, this, true);

    $(document).keydown(this.onKeyPress.bind(this));
    this.autoCompleteOnInputHandler = this.onInput.bind(this);
    this.autoCompleteOnKeyDownHandler = this.onKeyDown.bind(this);
    this.toggleAutoCompleteHandler(this.imvu.call('avatarNameAutoCompleteEnabled') && this.imvu.call('inAutoCompleteRollout'))
    this.eventBus.registerInScope('ChatTool', 'AvatarNameAutoCompleteSettingUpdated', function(evt, info) { 
        this.toggleAutoCompleteHandler(!!info.newValue);
    }.bind(this));
    
    this.eventBus.registerInScope('ChatTool', 'SessionWindow.InitiateNewChat', this.__initiateNewChat, 'SessionWindow', this);
    this.eventBus.registerInScope('ChatTool', 'SessionWindow.ParticipantJoined', this.__onNewParticipant, 'SessionWindow', this);
    this.eventBus.registerInScope('ChatTool', 'SessionWindow.ParticipantLeft', this.__onParticipantLeft, 'SessionWindow', this);
    this.eventBus.registerInScope('ChatTool', 'SessionWindow.ReceivedMessage', this.__onNewMessage, 'SessionWindow', this);
    this.eventBus.registerInScope('ChatTool', 'SessionWindow.MessageDelivered', this.__onMessageDelivered, 'SessionWindow', this);
    this.eventBus.registerInScope('ChatTool', 'SessionWindow.ReplaceRoom', this.__onReplaceRoom, 'SessionWindow', this);
    if (this.allowShopping) {
        this.eventBus.registerInScope('ChatTool', 'SessionWindow.TryProduct', this.__onTryProduct, 'SessionWindow', this);
        this.eventBus.registerInScope('ChatTool', 'SessionWindow.RecommendProduct', this.__onRecommendProduct, 'SessionWindow', this);
        this.eventBus.registerInScope('ChatTool', 'SessionWindow.PurchaseProduct', this.__onPurchaseProduct, 'SessionWindow', this);
        this.eventBus.registerInScope('ChatTool', 'SessionWindow.GiftProduct', this.__onGiftProduct, 'SessionWindow', this);
        this.eventBus.registerInScope('ChatTool', 'InventoryState.NewProducts', this.__onNewProduct);
        this.eventBus.registerInScope('ChatTool', 'AvatarClothingChanged', this.__onClothingChange,'SessionWindow', this);
    }

    var initialParticipants = this.imvu.call('getAllParticipants'),
        i;

    if (initialParticipants) {
        i = initialParticipants.length;
        while (i--) {
            if (this.localUserId != initialParticipants[i].userId) {
                this.__onNewParticipant(null, initialParticipants[i]);
            }
        }
    }

    var maxlength = this.imvu.call('getImvuConfigVariable', 'client.maximum_chat_length') || 5000;
    this.inputElement.setAttribute('maxlength', maxlength);

    this.inputElement.focus();

    this.$close = $(this.textChatElement).find('#close');
    if(!this.allowClose) { 
        this.$close.click(function() {
            this.imvu.call('closeActiveTool');
        }.bind(this));
    } else { 
        this.$close.hide();
    }
    
    $('body').click(function() {
        this.imvu.call('focusChat');
    }.bind(this));

    this.pendingOutgoingMessages = {};
    this.__applyConnectingStatus();
    this.eventBus.registerInScope('ChatTool', 'IMQ state change', this.__applyConnectingStatus, null, this);
}

ChatTool.prototype = {
    toggleAutoCompleteHandler:function(bool) { 
        $(this.inputElement).unbind('keydown', this.autoCompleteOnKeyDownHandler);
        $(this.inputElement).unbind('input', this.autoCompleteOnInputHandler);
        if(bool) { 
            $(this.inputElement).bind('keydown', this.autoCompleteOnKeyDownHandler);
            $(this.inputElement).bind('input', this.autoCompleteOnInputHandler);
        }
    },

    toggleTextSize: function(event) {
        this.largeText = !this.largeText;
        $(this.textChatElement).toggleClass('largeText', !!this.largeText);

        if (this.elementToScrollTo != null)
        {
            this.elementToScrollTo.scrollIntoView(false);
        }
    },

    autoGrowTextArea: function(event) {
        if (!event.shiftKey && event.keyCode == 13)
        {
            this.onSubmit();
            return;
        }

        var scrollH = this.inputElement.scrollHeight;
        if ( scrollH > this.inputElement.clientHeight ){
            this.inputElement.rows += 1;

        }

        this.refreshSize();

        if (this.elementToScrollTo != null)
        {
            this.elementToScrollTo.scrollIntoView(false);
        }
    },

    refreshSize: function() {
        if (this.expanded) {
            this.determineHistorySize();
        }
        else {
            this.setCollapsedSize();
        }
    },

    setCollapsedSize: function() {
        this.imvu.call('setWindowSize', this.FULL_WIDTH, this.formElement.offsetHeight + this.newWhisperIndicator.offsetHeight);
    },

    hideCTA: function() {
        $(this.ctaElement).hide();
    },

    inputElementGetsFocus: function() {
        this.hideCTA();
    },

    determineHistorySize: function() {
        this.historyElement.style.height = (this.FULL_HEIGHT - this.formElement.offsetHeight - this.header.offsetHeight - this.newWhisperIndicator.offsetHeight - 8) + "px";
    },

    invert: function() {
        var self = this;

        if ($(this.textChatElement).hasClass('inverted')) {
            $(this.textChatElement).removeClass('inverted');

            $('.who, .notice, .line:not(.whisper-new) .message', this.historyElement).each(function (index, el) {
                if (el.style.color == self._toCssColor([0, 0, 0])) {
                    el.style.color = self._toCssColor([255, 255, 255]);
                }
            });
        }
        else {
            $(this.textChatElement).addClass('inverted');

            $('.who, .notice, .line:not(.whisper-new) .message', this.historyElement).each(function (index, el) {
                if (el.style.color == self._toCssColor([255, 255, 255])) {
                    el.style.color = self._toCssColor([0, 0, 0]);
                }
            });
        }
    },

    _append: function(element, fromUserId) {
        var FUDGE_FACTOR = 10;
        var shouldScroll = (this.historyElement.scrollHeight <=
                            this.historyElement.scrollTop + this.historyElement.offsetHeight + FUDGE_FACTOR);

        this.historyElement.appendChild(element);
        if (shouldScroll || fromUserId == this.localUserId) {
            element.scrollIntoView(false);
        }
    },

    _newTextChatAutoScroll: function(element){
        this.elementToScrollTo = element;
        if (this.expanded){
            element.scrollIntoView(false);
        }
    },

    _toCssColor: function(c, adjustForInverted) {
        if (adjustForInverted) {
            if ($(this.textChatElement).hasClass('inverted')) {
                if (c[0] == 255 && c[1] == 255 && c[2] == 255) {
                    c = [0, 0, 0];
                }
            }
            else {
                if (c[0] == 0 && c[1] == 0 && c[2] == 0) {
                    c = [255, 255, 255];
                }
            }
        }
        return 'rgb(' + c.join(', ') + ')';
    },

    updateAvatarInfo: function(info) {
        var msg = _T("has joined the chat");
        this._appendForUser(info, msg, "notice");
    },

    removeAvatar: function(info) {
        var msg;
        if (info.isClosing) {
            if (info.allowLoadNewRoom) {
                msg = _T("has left their session. This session will automatically close in 2 minutes unless you load one of your own rooms");
            }
            else {
                msg = _T("has left their session. This session will automatically close in 2 minutes.");
            }
        } else {
            msg = _T("has left the chat");
        }
        this._appendForUser(info, msg, "notice");
    },

    __onNewParticipant: function(eventName, info) {
        IMVU.log('NEW PARTICIPANT: ' + JSON.stringify(info));
        this.chatParticipants[info.userId] = info;
        this.updateAvatarInfo(info);
    },

    __onReplaceRoom: function(eventName, info) {
        var msg = _T("has changed the room to: ");
        this._appendForUser(info, msg + info.roomName, 'notice');
    },

    showProductCard: function(productId) {
        this.imvu.call("showProductInfoDialog", parseInt(productId, 10));
    },
    
    showGiftDialog: function(productId) {
        giftData = {'id': productId};
        this.imvu.call('showGiftDialog', giftData);
    },
    
    __onTryProduct: function(eventName, info) {
        var msg = _T("tried on ");
        if(!_.has(this.pendedTryProductMessages, info.userId)) { 
            this.pendedTryProductMessages[info.userId] = {};
        }
        this.pendedTryProductMessages[info.userId][info.productId] = this.displayMessageForProduct.bind(this,info, msg);
    },

    __onRecommendProduct: function(eventName, info) {
        var msg = _T("suggested ");
        this.displayMessageForProduct(info, msg)
    },
    
    __onPurchaseProduct: function(eventName, info) {
        var msg = _T("bought ");
        this.displayMessageForProduct(info, msg)
        if(info.who === this.localUserId) {
            $('.product-'+info.productId).addClass('in-inventory');
        }
    },
    
    __onGiftProduct: function(eventName, info) {
        var msg = _T("gave ") + this.getPronoun({ 
            person: (info.recipientUserId == this.localUserId)?2:3,
            objective: true,
            capitalized: false
        }) + ' ';
        this.displayMessageForProduct(info, msg)
    },

    __onNewProduct: function(eventName, obj) {
        var newPids = obj.newProducts;
        _.each(newPids, function(pid) { 
            $('.product-'+pid).addClass('in-inventory');
        });
    },

    __onClothingChange: function(eventName, obj) {
        this.releasePentUpTryProductMessages(obj.userId, obj.productIds);
        if(obj.userId !== this.localUserId) { 
            return;
        }
        var productIds = obj.productIds;
        $('div.chat-product').removeClass('trying');
        _.each(productIds, function(pid) { 
            $('.product-'+pid).addClass('trying');
        }.bind(this));
    },

    releasePentUpTryProductMessages: function(userId, productIds) { 
        if(_.has(this.pendedTryProductMessages, userId)) { 
            _.each(productIds, function(pid) { 
                if(_.has(this.pendedTryProductMessages[userId], pid)) { 
                    this.pendedTryProductMessages[userId][pid].call();
                    delete this.pendedTryProductMessages[userId][pid];
                }
            }.bind(this));
        }
    },

    displayMessageForProduct: function(info, msg) {
        var $productIcon = $('<img>'),
            $productLink = $('<div>'),
            $buttonBar = $('<div>'),
            $giftButton = $('<div>'),
            $tryButton = $('<div>'),
            $buyButton = $('<div>'),
            $offButton = $('<div>'),
            $ownText = $('<div>'),
            $productEl = $('<div>'),
            $apUpsellButton = $('<div>'),
            $buttonWrapper = $('<div>');

        var shouldSeeAPUpsell = info.productMature === 'Y' && 
            !this.imvu.call('hasAccessPass') && 
            !this.imvu.call('isTeen');

        $productEl.addClass('chat-product product-'+info.productId);
        $productEl.toggleClass('in-inventory',info.productOwned);
        $productEl.toggleClass('purchasable',!!info.purchasable);
        $productEl.toggleClass('trying', !!info.productWorn);
        $productEl.toggleClass('ap-only', shouldSeeAPUpsell);
        
        if (info.userId !== this.localUserId) {            
            var color = this._toCssColor(info.nameTagColor, true);
            var $name = $('<span>')                
                .addClass('wearer-name')                
                .css('color', color)
                .text(info.who)
                .click(function() { 
                    this.imvu.call('showAvatarCard', info.userId, {});
                }.bind(this));
            $productEl.append($name);
        }
               
        $productIcon.attr('src', shouldSeeAPUpsell ? "img/ap_upsell_blur.png" : info.productImage);
        $productIcon.addClass('product-icon').click(this.showProductCard.bind(this, info.productId));
        $productIcon.addClass('ui-event').attr('data-ui-name', 'ProductIcon');

        $productLink.append(info.productName);
        $productLink.addClass('product-link').click(this.showProductCard.bind(this, info.productId));
        $productLink.addClass('ui-event').attr('data-ui-name', 'ProductLink');
        $apUpsellButton
            .addClass('imvu-button')
            .addClass('level2')
            .addClass('ap-upsell-button')
            .addClass('ui-event')
            .attr('data-ui-name', 'shop_together_ap_upsell')
            .text(_T('Get Access Pass'));
        $apUpsellButton.click(function() {
            this.imvu.call('launchUrl', 'http://www.imvu.com/accesspass/?source=null_search');
        }.bind(this));
            
        ellipsize($productLink, 98);

        $giftButton.append(_T('Gift'));
        $giftButton.addClass('gift-link').click(this.showGiftDialog.bind(this, info.productId));
        $giftButton.addClass('ui-event').attr('data-ui-name', 'Gift');
        
        $tryButton.append(_T('Try'));
        $tryButton.addClass('try-link').click(function(){
            this.imvu.call("tryOnProduct", parseInt(info.productId, 10));
        }.bind(this));
        $tryButton.addClass('ui-event').attr('data-ui-name', 'Try');
        
        $buyButton.append(_T('Buy'));
        $buyButton.addClass('buy-link').click(this.showProductCard.bind(this, info.productId));
        $buyButton.addClass('ui-event').attr('data-ui-name', 'Buy');

        $offButton.append(_T('Off'));
        $offButton.addClass('off-link clickable').click(function() { 
            this.imvu.call('takeOffProduct', ''+info.productId);
        }.bind(this));
        $offButton.addClass('ui-event').attr('data-ui-name', 'Off');


        $ownText.append(_T('Own'));
        $ownText.addClass('you-own-this')

        $buttonBar.addClass('button-bar');
        $buttonWrapper.addClass('button-wrapper');

        msg = (info.userId !== this.localUserId) ? msg : _T("You ") + msg;
        msg = (shouldSeeAPUpsell) ? msg + _T(" an AP item") : msg;
        
        var $action = $('<div>').addClass('who').append(msg);       
        $productEl.append($action);
        $buttonBar.append($productIcon);
        $productEl.append($productLink);        
        $buttonWrapper.append($giftButton);
        $buttonWrapper.append($tryButton);
        $buttonWrapper.append($offButton);
        $buttonWrapper.append($buyButton);
        $buttonWrapper.append($ownText);
        $buttonBar.append($buttonWrapper);
        $productEl.append($buttonBar);
        $productEl.append($apUpsellButton);

        //this._appendForUser(info, msg, 'notice', [$productEl[0]]);
        this._append($productEl[0], 0);

    },

    __onParticipantLeft: function(eventName, info) {
        var who = info.who;

        delete this.chatParticipants[info.userId];

        if (who != '<unknown>') {
            this.removeAvatar(info);
        }
    },

    __onNewMessage: function(eventName, info) {
        this._appendForUser(info, info.message, "message");
    },

    __onMessageDelivered: function(eventName, info) {
        $(this.pendingOutgoingMessages[info.outgoingMessageId]).removeClass('pending');
        $('.cancel', this.pendingOutgoingMessages[info.outgoingMessageId]).unbind('click');
        $('.retry', this.pendingOutgoingMessages[info.outgoingMessageId]).unbind('click');
        delete this.pendingOutgoingMessages[info.ougoingMessageId];
    },

    _canWhisperToUser: function(userId) {
        if (this._participantInChat(userId) && userId != this.localUserId) {
            return (this.imvu.call('hasVIPPass') || this.whisperers[userId]);
        }

        return false;
    },

    _participantInChat: function(userId) {
        return this.chatParticipants.hasOwnProperty(userId);
    },

    _createNameNode: function(elementType, nameTagColor, who, info, messageClass) {
        var name = document.createElement(elementType);
        name.className = 'who';
        if (!this._isOutgoingMessage(info)) {
            name.style.color = this._toCssColor(nameTagColor, true);
        }
        name.appendChild(document.createTextNode(who));
        $(name).mouseover(this.showAvatarButtons.bind(this, name, info, messageClass));
        return name;
    },

    _canPostNarrate: function(who, msg) {        
        return msg.slice(0, 4) === '/me ';
    },

    _isOutgoingMessage: function(info) {
        return (typeof(info.outgoingMessageId) !== 'undefined') && (info.outgoingMessageId !== null);
    },

    _appendForUser: function(info, msg, messageClass, extraElements) {
        var who = info.who,
            nameTagColor = info.nameTagColor,
            name,
            whisperIcon,
            tooltip,
            hovertip,
            messageNode,
            whisperBack,
            lineElement;

        if (typeof(extraElements) === 'undefined') {
            extraElements = [];
        }

        var isStatus = this._canPostNarrate(who, msg);           
        if (isStatus) {
            msg = msg.substring(4);
        }
        name = this._createNameNode('span', nameTagColor, who, info, messageClass);
        messageNode = document.createElement('span');

        messageNode.className = messageClass;
        $(messageNode).append(IMVU.Client.util.linkifyWithEmoji(msg));
        

        if (messageClass == "notice" || isStatus) {
            messageNode.style.color = this._toCssColor(nameTagColor, !info.to);
        }

        // We could insert the ": " with CSS, but then it would not appear in the clipboard
        // when the customer copies from the chat history. -- andy 9 July 2010

        lineElement = document.createElement('div');
        lineElement.className = 'line';
        if (this._isOutgoingMessage(info)) {
            $(lineElement).addClass('outgoing');
            $(lineElement).addClass('pending');
            this.pendingOutgoingMessages[info.outgoingMessageId] = lineElement;

            var cancelElement = document.createElement('span');
            cancelElement.className = 'cancel';
            $(cancelElement).click(function () {
                this.historyElement.removeChild(lineElement);
                this.imvu.call('cancelChatMessage', info.outgoingMessageId);
            }.bind(this));
            lineElement.appendChild(cancelElement);

            var retryElement = document.createElement('span');
            retryElement.className = 'retry';
            $(retryElement).click(function() {
                this.imvu.call('imqReconnect');
            }.bind(this));
            lineElement.appendChild(retryElement);
        }

        lineElement.appendChild(name);
        if (messageClass == "message" && !isStatus) {
            if (!info.to) {
                lineElement.appendChild(document.createTextNode(': '));
            } else if (info.to != this.localUserId) {
                lineElement.appendChild(document.createTextNode(' > '));
                var to = document.createElement('strong');
                to.style.color = (this._canWhisperToUser(info.to)) ? this._toCssColor(this.chatParticipants[info.to].nameTagColor) : '';
                to.innerHTML = info.toName;
                lineElement.appendChild(to);
                lineElement.appendChild(document.createTextNode(': '));
            } else if (info.to == this.localUserId) {
                this.whisperers[info.userId] = true;
                lineElement.appendChild(document.createTextNode(' '+_T("whispers")+': '));
            }
        } else {
            lineElement.appendChild(document.createTextNode(" "));
        }
        lineElement.appendChild(messageNode);
                
        if (info.to) {
            messageNode.style.color = '#000';
            messageNode.style.backgroundColor = this._toCssColor(nameTagColor);
            $(lineElement).addClass('whisper');
            
            // HACK: avoid a rendering clipping bug with FF and italics
            $(lineElement).find('.who')[0].innerHTML += '&nbsp;';
            $(lineElement).find('.message')[0].innerHTML += '&nbsp;';
        }
        
        if (isStatus) {            
            $(lineElement).addClass('status');
            
            // HACK: avoid a rendering clipping bug with FF and italics
            $(lineElement).find('.who')[0].innerHTML += '&nbsp;';
            $(lineElement).find('.message')[0].innerHTML += '&nbsp;';
        }

        for each (var extraElement in extraElements) {
            lineElement.appendChild(extraElement);
        }

        this._append(lineElement, info.userId);
        
        IMVU.Client.util.turnLinksIntoLaunchUrls(lineElement, this.imvu);
    },
    getPronoun: function(params) { 
        _.defaults(params, { 
            person: 2,
            objective: false,
            capitalized: true
        });

        //info.userId == this.localUserId
        var pronoun = '';
        if(params.person === 2) { 
            pronoun = _T('you');
        } else { 
            if(params.objective) { 
                pronoun = _T('them');
            } else { 
                pronoun = _T('they');
            }
        }

        if(params.capitalized) { 
            pronoun = _.str.capitalize(pronoun);
        }
        return pronoun;
    },

    hideTool: function(event) {
        $(this.textChatElement).addClass('collapsed');
        this.expanded = false;
        this.refreshSize();

        this.imvu.call('setPref', 'newTextChatExpanded', false);
    },

    showTool: function(event) {
        $(this.textChatElement).removeClass('collapsed');
        this.imvu.call('setWindowSize', this.FULL_WIDTH, this.FULL_HEIGHT);
        this.expanded = true;
        this.refreshSize();
        if (this.elementToScrollTo != null) {
            this.elementToScrollTo.scrollIntoView(false);
        }

        this.imvu.call('setPref', 'newTextChatExpanded', true);
    },

    enoughParticipantsForWhispering: function() {
        var nonPilotParticipants = _.filter(this.chatParticipants, function(info, userId) { return userId != this.localUserId; }, this);
        return nonPilotParticipants.length > 1;
    },

    showAvatarButtons: function(el, info, messageClass) {
        var parent = $(el).parent();
        if (parent.hasClass('outgoing') && parent.hasClass('pending')) {
            return;
        }

        var $infoIcon,
            whisperIcon,
            $flagIcon,
            tooltip,
            hovertip;
            canWhisper = this._participantInChat(info.userId) && this.enoughParticipantsForWhispering(),
            canAddFriend = this._participantInChat(info.userId) && !this.imvu.call("getBuddyType", info.userId);

        tooltip = document.createElement('span');
        tooltip.className = 'tooltip';

        if ((info.userId != this.localUserId) && (messageClass == 'message')) {
            $flagIcon = $('<a></a>');
            $flagIcon.addClass('flag-icon').text(' ');
            $flagIcon.appendTo(tooltip);
            $flagIcon.click(function(evt) {
                this.imvu.call('showChatLogFlaggingDialog', info.userId, info.index);
            }.bind(this));
        }

        $infoIcon = $('<a/>');
        $infoIcon.addClass('info-icon');
        $infoIcon.click(function() {
            this.imvu.call('showAvatarCard', info.userId, {});
        }.bind(this));
        $(tooltip).append($infoIcon);

        if (canWhisper) {
            whisperIcon = document.createElement('a');
            whisperIcon.className = "whisper-icon";
            whisperIcon.innerHTML = _T("Whisper");

            $(whisperIcon).click(this.enterWhisper.bind(this, info.userId, info.who));
            $(whisperIcon).addClass('ui-event');
            $(whisperIcon).attr('data-ui-name', 'whisper_icon');
            tooltip.appendChild(whisperIcon);
        }
                
        if ($(el).parent().hasClass('status')) {
            narrateIcon = document.createElement('a');
            narrateIcon.className = 'narrate-icon';
            narrateIcon.innerHTML = _T("Narrate");
            
            $(narrateIcon).click(this.narrate.bind(this));
            $(narrateIcon).addClass('ui-event');
            $(narrateIcon).attr('data-ui-name', 'narrate_icon');
            tooltip.appendChild(narrateIcon);
        }

        if (canAddFriend) {
            addFriendIcon = document.createElement('a');
            addFriendIcon.className = "addfriend-icon";
            addFriendIcon.innerHTML = _T("Add Friend");

            $(addFriendIcon).click(this.addFriend.bind(this, info.userId, info.who, info.nameTagColor));
            $(addFriendIcon).addClass('ui-event');
            $(addFriendIcon).attr('data-ui-name', 'add_friend_icon');
            tooltip.appendChild(addFriendIcon);
        }

        hovertip = document.createElement('span');
        hovertip.className = 'hovertip';
        hovertip.style.color = el.style.color;
        hovertip.appendChild(el.cloneNode(true));
        hovertip.appendChild(document.createTextNode(' '));
        hovertip.appendChild(tooltip);
        $(hovertip).mouseout(function (event) { this.hideAvatarButtons(event, el); }.bind(this));

        el.parentNode.insertBefore(hovertip, el.nextSibling);
    },

    hideAvatarButtons: function(event, el) {
        var relatedClassName = '';
        if (event.relatedTarget) {
            if (event.relatedTarget instanceof HTMLElement) {
                relatedClassName = event.relatedTarget.className.replace(" ui-event", "");
            }
            if (event.currentTarget.className == 'hovertip'
                && event.relatedTarget
                && !/^(tooltip|hovertip|info-icon|flag-icon|whisper-icon|narrate-icon|addfriend-icon)$/.test(relatedClassName)
            ) {
                var hovertip = el.parentNode.querySelector('.hovertip');
                try {
                    el.parentNode.removeChild(hovertip);
                } catch(e) {
                }
            }
        }
    },

    narrate: function() {        
        if (this.imvu.call('hasVIPPass') || this.imvu.call('hasAccessPass')) {
            if ($(this.inputElement).hasClass('hint')) {
                $(this.inputElement).removeClass('hint');
                this.inputElement.value = '/me ';
                $(this.inputElement).focus();
            } else {
                var msg = this.inputElement.value;
                if (msg.slice(0, 4) !== '/me ') {
                    this.inputElement.value = '/me ' + this.inputElement.value;
                }
            }
            
        } else {
            this.imvu.call('showVipUpsell');
        }
    },
    
    enterWhisper: function(userId, who) {
        if (this._canWhisperToUser(userId)) {
            color = 'color: ' + this._toCssColor(this.chatParticipants[userId].nameTagColor);
            if (!$(this.textChatElement).hasClass('whispering')) {
                 $(this.textChatElement).addClass('whispering');
            }

            var whisperIndicator = this.textChatElement.querySelector('.whisper-indicator');
            whisperIndicator.innerHTML = _T("Whispering to")+' <b style="' + color + '">' + who + '</b>:';
            this.whisperTargetId = userId;
            this.whisperTargetName = who;
        } else {
            this.imvu.call('showVipUpsell');
        }
    },

    cancelWhisper: function() {
        var whisperIndicator = document.querySelector('.whisper-indicator');
        $(this.textChatElement).removeClass('whispering');

        this.whisperTargetId = 0;
    },

    addFriend: function(userId, who, color) {
        this.imvu.call("addBuddy", userId, 'client chat');
        this._appendForUser({ who: who, userId: userId, nameTagColor: color }, _T("has been sent a friend request."), "notice");
    },

    onSubmitForm: function(evt){
        evt.preventDefault();
        this.onSubmit();
    },

    onSubmit: function() {
        var line = this.inputElement.value;

        // line is blank or whitespace-only
        if (/^\s*$/.test(line)) {
            return;
        }

        this.inputElement.value = '';

        if (!this.whisperTargetId || (this.whisperTargetId && this._canWhisperToUser(this.whisperTargetId))) {
            // You can uncomment this if you want to fiddle around with the chat tool in FireFox. -- andy 17 May 2010
            //this.__onNewMessage(null, {who:'me', message:line, nameTagColor:[255,255,255]});
            this.imvu.call('notifyChatMessage', line, this.whisperTargetId);
        } else {
            this._appendForUser({ who: this.whisperTargetName, userId: this.whisperTargetId, nameTagColor: [255,0,0] }, _T("did not receive your whisper because they left the chat."), "notice");
        }
    },

    keyIsEnter: function(keyCode) {
        return (keyCode == 10) || (keyCode == 13);
    },

    keyIsModified: function(keyEvt) {
        return (keyEvt.ctrlKey || keyEvt.altKey || keyEvt.metaKey);
    },

    keyIsReadOnlyTextAccelerator: function(keyEvt) {
        //HACK: this is pretty gross
        passKeyCodes = { 65 : 'a',
                         67 : 'c',
                         17 : 'shift',
                         18 : 'ctrl' };
        return this.keyIsModified(keyEvt) && (keyEvt.keyCode in passKeyCodes);
    },

    findName: function(search) { 
        var search = search.toLowerCase();
        search = escapeForRegExp(search);
        var names = _.chain(this.chatParticipants).values().pluck('who').value();
        for(var i = 0; i < names.length; i++) { 
            var name = names[i].toLowerCase();
            if(name.search(search) === 0) { 
                return names[i];
            }
            if(name.replace(/^guest_/,'').search(search) === 0) { 
                return names[i].replace(/^Guest_/,'');
            }
        }
        return false;
    },
    getLastWord: function() { 
        function reverse(s){
            return s.split("").reverse().join("");
        }
        var curInput = this.inputElement.value;
        var lengthOfLastWord = reverse(curInput).search(/[\.,-\/#!$%\^&\*;:{}=\-`~()\ \"\']/);//to do look for all punc
        if(lengthOfLastWord === -1) { 
            lengthOfLastWord = curInput.length;
        }
        var lastWord = curInput.slice(-lengthOfLastWord);
        if(lastWord[0] === '@') { 
            lastWord = lastWord.slice(1);
        }
        return lastWord;
    },
    shouldAutoComplete: function(TAB_CLICKED, lastWord) { 
        if(this.isCursorAtEndOfInput()) { 
            return false;
        }
        if(lastWord.length === 0)  { //string too short
            return false;
        }
        var hasAtSymbol = '@' === this.inputElement.value.slice(-lastWord.length-1).slice(0,-lastWord.length);
        return TAB_CLICKED || lastWord.length >= 4 || hasAtSymbol; //@ starts autocompletion immediately
    },
    setInputSelectionRange: function(TAB_CLICKED, lastWord, match) { 
        var length = this.inputElement.value.length;
        var startSelect = length;
        if(!TAB_CLICKED) {
            startSelect -= match.length - lastWord.length;
        }
        this.inputElement.setSelectionRange(startSelect, length);
    },
    attemptRevertRecommendation: function(charAdded) { 
        //Check to see if the patch is valid
        if(!(this.pristineLastWord && this.pristineLastWord.length)) { 
            return;
        }
        var inputEndLength = this.pristineLastWord.length+((charAdded)?1:(this.inputElement.value.length-this.getStartOfSelection()));
        try { 
            var inputEnd = this.inputElement.value.slice(-inputEndLength, ((charAdded)?-1:this.getStartOfSelection())).split('');

            _(this.pristineLastWord).each(function(letter, i) { 
                if(inputEnd[i].toLowerCase() !== letter.toLowerCase()) { 
                    throw "Patch mismatch";
                }
            });
        } catch(err) { 
            console.log('Avatar Name Autocomplete: Unable to apply patch');
            this.clearPristineLastWord();
            return;
        }
        var cleanInputText = this.inputElement.value.slice(0,-inputEndLength);
        var finalLetter = this.inputElement.value.slice(-1);
        this.inputElement.value = cleanInputText + this.pristineLastWord.join('') + ((charAdded)?finalLetter:'');
        this.clearPristineLastWord();

    },
    onKeyDown: function(e) { 
        this.DELETE_CLICKED = e.which === 8;
        this.ESCAPE_CLICKED = e.which === 27;
        this.TAB_CLICKED = e.which === 9;
        if(this.ESCAPE_CLICKED) { 
            this.attemptRevertRecommendation(false/*charAdded*/);
        }
        if(this.TAB_CLICKED) { 
            this.onTabClicked();
        }
    },
    onTabClicked: function() { 
        var lastWord = this.getLastWord();
        var match = this.getRecommendation(lastWord);
        if(match) { 
            this.insertRecommendation(lastWord, match);
            this.inputElement.value += ' ';
            this.setInputSelectionRange(true/*tab clicked*/, lastWord, match);
        }
    },
    getRecommendation: function(lastWord) { 
        if(!this.shouldAutoComplete(this.TAB_CLICKED, lastWord)) { 
            return '';
        }
        var match = this.findName(lastWord);
        return match;
    },
    onInput: function(e) { 
        if(this.DELETE_CLICKED) { 
            this.attemptRevertRecommendation(false/*charAdded*/);
            return;
        }
        var lastWord = this.getLastWord();
        var match = this.getRecommendation(lastWord);
        if(match) { 
            this.insertRecommendation(lastWord, match);
            this.setInputSelectionRange(this.T, lastWord, match);
        } else { 
            this.attemptRevertRecommendation(true/*charAdded*/);
        }
    },
    getStartOfSelection: function() { 
        return _.min([this.inputElement.selectionStart, this.inputElement.selectionEnd]);
    },
    isCursorAtEndOfInput: function() { 
        var input = this.inputElement;
        return (input.selectionEnd === input.selectionStart && input.selectionStart === input.value.length+1);
    },
    clearPristineLastWord: function() { 
        this.pristineLastWord.length = 0;
    },
    storePristineLastWord: function(lastWord) { 
        this.pristineLastWord = this.pristineLastWord || [];
        try { 
            _(lastWord.split('')).each(function(letter, i) { 
                if(this.pristineLastWord.length <= i) { 
                    this.pristineLastWord.push(letter);
                }
                if(this.pristineLastWord[i].toLowerCase() !== letter.toLowerCase()) { 
                    throw "pristineLastWord fallen out of sync";
                }
            }, this);
        } catch(err) { 
            this.pristineLastWord.length = 0;
            _(lastWord.split('')).each(function(letter) { 
                this.pristineLastWord.push(letter);
            }, this);
        }
    },
    insertRecommendation: function(lastWord, match) { 
        this.storePristineLastWord(lastWord);
        this.inputElement.value = this.inputElement.value.slice(0,-lastWord.length)+match;
    },
    onKeyPress: function(evt) {
        if(evt.which === 9) { //tab
            evt.preventDefault();
        } 
        if (!this.keyIsReadOnlyTextAccelerator(evt) && evt.target.tagName != 'INPUT') {
            this.inputElement.focus();
        }

        if (!this.keyIsEnter(evt.keyCode) && !this.whisperTargetId) {
            if (this.inputElement.value.length == 0 && this.textBubbleActive) {
                this.textBubbleActive = false;
                var userId = this.imvu.call("getCustomerId");
                this.imvu.call("notifyChatMessage", "*msg EraseText 2 " + userId + " 0 0", 0);
            } else if (!this.textBubbleActive && this.inputElement.value.length != 0) {
                this.textBubbleActive = true;
                var userId = this.imvu.call("getCustomerId");
                this.imvu.call("notifyChatMessage", "*msg BeginText 2 " + userId + " 0 0", 0);
            }
        }
    },

    onHistoryContextMenu: function(evt) {
        YAHOO.util.Event.preventDefault(evt);
        YAHOO.util.Event.stopPropagation(evt);

        this.imvu.call('showHistoryContextMenu', evt.pageX, evt.pageY);
    },

    onInputContextMenu: function(evt) {
        YAHOO.util.Event.preventDefault(evt);
        YAHOO.util.Event.stopPropagation(evt);

        this.imvu.call('showInputContextMenu', evt.pageX, evt.pageY);
    },

    pasteText: function(text) {
        var startPos = this.inputElement.selectionStart;
        var endPos = this.inputElement.selectionEnd;
        var line = this.inputElement.value;

        this.inputElement.value = line.substring(0, startPos) + text + line.substring(endPos);
        this.inputElement.selectionStart = this.inputElement.selectionEnd = startPos + text.length;
    },

    hideMessageTray: function(){
        this.messageTrayEl.style.display = 'none';
        this.messageTrayOverlayEl.style.display = 'none';
        $(this.messageTrayEl).removeClass('flashing');

        if (this.messageQueue[0]){
            this.animateNextMessage();
        } else {
            this.animating = false;
        }
        this.updateWindowSize();
    },

    __initiateNewChat: function(evt, info) {
        this.historyElement.innerHTML = '';
        if (info.roomInstanceId) {
            var msg = _T("came from");
            var link = document.createElement('span');
            link.appendChild(document.createTextNode(info.roomName));
            $(link).addClass('room-link');
            $(link).click(function(){
                this.imvu.call('joinPublicRoom', info.roomInstanceId);
            }.bind(this));
            this._appendForUser(info, msg, 'notice', [link]);
        }
    },

    __applyConnectingStatus: function() {
        var state = this.imvu.call('imqState');
        switch (state[0]) {
            case 'not_connected':
                $(this.historyElement).removeClass('reconnecting');
                $(this.historyElement).addClass('disconnected');
                break;
            case 'connecting':
            case 'authenticating':
                $(this.historyElement).removeClass('disconnected');
                $(this.historyElement).addClass('reconnecting');
                break;
            case 'connected':
                $(this.historyElement).removeClass('disconnected');
                $(this.historyElement).removeClass('reconnecting');
                break;
        }
    }
};
