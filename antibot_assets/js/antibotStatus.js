/* IMVU room antibot patch — protection shield, boot log, and whitelist UI. */
(function () {
    if (!window.IMVU) {
        window.IMVU = {};
    }
    if (!IMVU.Client) {
        IMVU.Client = {};
    }
    if (IMVU.Client.AntibotStatus) {
        return;
    }

    var MARKER = 'imvu-antibot-status-installed';
    var BOOT_PAGE_SIZE = 10;
    var WHITELIST_PAGE_SIZE = 6;
    var CANDIDATE_LIMIT = 8;
    var POPUP_WIDTH = 280;
    var POPUP_HEIGHT = 220;
    var REASON_LABELS = {
        promo_message: 'Promo / spam message',
        guest_spam_profile: 'Disposable guest account'
    };

    function reasonLabel(reason) {
        return REASON_LABELS[reason] || reason || 'Unknown';
    }

    function escapeHtml(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function callImvu(method, arg1, arg2, arg3) {
        if (!window.imvu || !window.imvu.call) {
            return null;
        }
        try {
            switch (arguments.length) {
            case 1:
                return window.imvu.call(method);
            case 2:
                return window.imvu.call(method, arg1);
            case 3:
                return window.imvu.call(method, arg1, arg2);
            default:
                return window.imvu.call(method, arg1, arg2, arg3);
            }
        } catch (e) {
            return null;
        }
    }

    function isWhitelistedUser(userId, whitelist) {
        var i;
        for (i = 0; i < whitelist.length; i++) {
            if (String(whitelist[i].userId) === String(userId)) {
                return true;
            }
        }
        return false;
    }

    function attach(textChatRoot, eventBus) {
        if (!textChatRoot || textChatRoot.getAttribute(MARKER) === '1' || !eventBus) {
            return;
        }

        var inputRow = textChatRoot.querySelector('#inputRow') || document.getElementById('inputRow');
        var sendButton = inputRow
            ? (inputRow.querySelector('#send-button') || document.getElementById('send-button'))
            : document.getElementById('send-button');
        if (!inputRow || !sendButton) {
            return;
        }

        var boots = [];
        var whitelist = [];
        var open = false;
        var activeTab = 'boots';
        var bootPage = 0;
        var whitelistPage = 0;
        var localUserId = callImvu('getCustomerId');

        var button = document.createElement('button');
        button.type = 'button';
        button.id = 'antibot-button';
        button.className = 'imvu-antibot-button inactive';
        button.innerHTML =
            '<span class="imvu-antibot-icon" aria-hidden="true">&#x1f6e1;</span>' +
            '<span class="imvu-antibot-on">ON</span>';
        button.title = 'Protection inactive';
        inputRow.insertBefore(button, sendButton);

        var popup = document.createElement('div');
        popup.className = 'imvu-antibot-popup';
        popup.setAttribute('aria-hidden', 'true');
        popup.style.display = 'none';
        popup.innerHTML =
            '<button type="button" class="imvu-antibot-popup-close" title="Close">&times;</button>' +
            '<div class="imvu-antibot-popup-head">' +
            '<div class="imvu-antibot-popup-title">Room anti-bot</div>' +
            '<div class="imvu-antibot-tabs">' +
            '<button type="button" class="imvu-antibot-tab active" data-tab="boots">Boot log</button>' +
            '<button type="button" class="imvu-antibot-tab" data-tab="whitelist">Whitelist</button>' +
            '</div></div>' +
            '<div class="imvu-antibot-popup-body"></div>';
        document.body.appendChild(popup);
        var body = popup.getElementsByClassName('imvu-antibot-popup-body')[0];
        var tabButtons = popup.getElementsByClassName('imvu-antibot-tab');

        function setActive(active) {
            button.className = 'imvu-antibot-button ' + (active ? 'active' : 'inactive');
            button.title = active
                ? 'Protection active — click for boot log and whitelist'
                : 'Protection inactive — you cannot boot users in this room';
        }

        function setTab(tabName) {
            activeTab = tabName;
            var i;
            for (i = 0; i < tabButtons.length; i++) {
                var tab = tabButtons[i];
                if (tab.getAttribute('data-tab') === tabName) {
                    tab.className = 'imvu-antibot-tab active';
                } else {
                    tab.className = 'imvu-antibot-tab';
                }
            }
            refreshPopup();
        }

        function positionPopupNearButton() {
            var rect = button.getBoundingClientRect ? button.getBoundingClientRect() : null;
            var popupWidth = POPUP_WIDTH;
            var popupHeight = POPUP_HEIGHT;
            var viewportWidth = document.documentElement.clientWidth || document.body.clientWidth || 800;
            var viewportHeight = document.documentElement.clientHeight || document.body.clientHeight || 600;
            var left = 8;
            var top = 8;
            if (rect) {
                left = rect.right - popupWidth;
                top = rect.top - popupHeight - 8;
                if (top < 8) {
                    top = rect.bottom + 8;
                }
            }
            if (left < 8) {
                left = 8;
            }
            if (left + popupWidth > viewportWidth - 8) {
                left = viewportWidth - popupWidth - 8;
            }
            if (top < 8) {
                top = 8;
            }
            if (top + popupHeight > viewportHeight - 8) {
                top = Math.max(8, viewportHeight - popupHeight - 8);
            }
            popup.style.left = left + 'px';
            popup.style.top = top + 'px';
        }

        function setPopupVisible(visible) {
            popup.setAttribute('aria-hidden', visible ? 'false' : 'true');
            popup.style.display = visible ? 'block' : 'none';
        }

        function formatBootsPanel() {
            var html = '<div class="imvu-antibot-panel" data-panel="boots">';
            if (!boots || !boots.length) {
                html += '<div class="imvu-antibot-empty">No bots booted this session.</div>';
            } else {
                var total = boots.length;
                var totalPages = Math.ceil(total / BOOT_PAGE_SIZE);
                if (bootPage >= totalPages) {
                    bootPage = totalPages - 1;
                }
                if (bootPage < 0) {
                    bootPage = 0;
                }
                var start = bootPage * BOOT_PAGE_SIZE;
                var end = Math.min(start + BOOT_PAGE_SIZE, total);
                if (totalPages > 1) {
                    html += '<div class="imvu-antibot-pager">';
                    html += 'Showing ' + (start + 1) + '\u2013' + end + ' of ' + total;
                    if (bootPage > 0) {
                        html += ' <button type="button" class="imvu-antibot-page-btn" data-page="' +
                            (bootPage - 1) + '">Prev</button>';
                    }
                    if (bootPage < totalPages - 1) {
                        html += ' <button type="button" class="imvu-antibot-page-btn" data-page="' +
                            (bootPage + 1) + '">Next</button>';
                    }
                    html += '</div>';
                }
                html += '<ul class="imvu-antibot-list">';
                var i;
                for (i = start; i < end; i++) {
                    var entry = boots[i];
                    var name = entry.avatarName || ('User ' + entry.userId);
                    html += '<li>';
                    html += '<span class="imvu-antibot-name">' + escapeHtml(name) + '</span>';
                    html += '<span class="imvu-antibot-reason">' + escapeHtml(reasonLabel(entry.reason)) + '</span>';
                    if (!isWhitelistedUser(entry.userId, whitelist)) {
                        html += '<span class="imvu-antibot-list-actions">';
                        html += '<button type="button" class="imvu-antibot-trust-btn" data-user-id="' +
                            escapeHtml(entry.userId) + '" data-user-name="' + escapeHtml(name) +
                            '">Whitelist</button>';
                        html += '</span>';
                    } else {
                        html += '<span class="imvu-antibot-list-actions imvu-antibot-trusted-label">Trusted</span>';
                    }
                    html += '</li>';
                }
                html += '</ul>';
            }
            html += '</div>';
            return html;
        }

        function formatWhitelistCandidates() {
            var participants = callImvu('getAllParticipants') || [];
            var html = '';
            var shown = 0;
            var hidden = 0;
            var i;
            for (i = 0; i < participants.length; i++) {
                var person = participants[i];
                if (!person || !person.userId) {
                    continue;
                }
                if (String(person.userId) === String(localUserId)) {
                    continue;
                }
                if (isWhitelistedUser(person.userId, whitelist)) {
                    continue;
                }
                if (shown >= CANDIDATE_LIMIT) {
                    hidden++;
                    continue;
                }
                var label = person.who || ('User ' + person.userId);
                html += '<li>';
                html += '<span class="imvu-antibot-name">' + escapeHtml(label) + '</span>';
                html += '<span class="imvu-antibot-list-actions">';
                html += '<button type="button" class="imvu-antibot-whitelist-add-btn" data-user-id="' +
                    escapeHtml(person.userId) + '" data-user-name="' + escapeHtml(label) + '">Add</button>';
                html += '</span></li>';
                shown++;
            }
            if (!shown && !hidden) {
                html += '<li class="imvu-antibot-empty-row">Everyone here is already trusted.</li>';
            } else if (hidden) {
                html += '<li class="imvu-antibot-empty-row">+' + hidden +
                    ' more in this room (add from boot log).</li>';
            }
            return html;
        }

        function formatWhitelistPanel() {
            var html = '<div class="imvu-antibot-panel" data-panel="whitelist">';
            html += '<div class="imvu-antibot-section-title">Add from this room</div>';
            html += '<ul class="imvu-antibot-list imvu-antibot-whitelist-candidates">';
            html += formatWhitelistCandidates();
            html += '</ul>';

            var saved = [];
            var builtinCount = 0;
            var entries = whitelist || [];
            var i;
            for (i = 0; i < entries.length; i++) {
                if (entries[i].builtin) {
                    builtinCount++;
                } else {
                    saved.push(entries[i]);
                }
            }

            html += '<div class="imvu-antibot-section-title">Your saved whitelist</div>';
            if (builtinCount) {
                html += '<div class="imvu-antibot-note">' + builtinCount +
                    ' built-in account' + (builtinCount === 1 ? '' : 's') +
                    ' are always trusted.</div>';
            }
            if (!saved.length) {
                html += '<div class="imvu-antibot-empty">No saved entries yet. Use Add or Whitelist.</div>';
            } else {
                var savedTotal = saved.length;
                var savedPages = Math.ceil(savedTotal / WHITELIST_PAGE_SIZE);
                if (whitelistPage >= savedPages) {
                    whitelistPage = savedPages - 1;
                }
                if (whitelistPage < 0) {
                    whitelistPage = 0;
                }
                var savedStart = whitelistPage * WHITELIST_PAGE_SIZE;
                var savedEnd = Math.min(savedStart + WHITELIST_PAGE_SIZE, savedTotal);
                if (savedPages > 1) {
                    html += '<div class="imvu-antibot-pager">';
                    html += 'Saved ' + (savedStart + 1) + '\u2013' + savedEnd + ' of ' + savedTotal;
                    if (whitelistPage > 0) {
                        html += ' <button type="button" class="imvu-antibot-page-btn" data-list="whitelist" data-page="' +
                            (whitelistPage - 1) + '">Prev</button>';
                    }
                    if (whitelistPage < savedPages - 1) {
                        html += ' <button type="button" class="imvu-antibot-page-btn" data-list="whitelist" data-page="' +
                            (whitelistPage + 1) + '">Next</button>';
                    }
                    html += '</div>';
                }
                html += '<ul class="imvu-antibot-list imvu-antibot-whitelist-trusted">';
                for (i = savedStart; i < savedEnd; i++) {
                    var item = saved[i];
                    var label = item.avatarName || ('User ' + item.userId);
                    html += '<li>';
                    html += '<span class="imvu-antibot-name">' + escapeHtml(label) + '</span>';
                    html += '<span class="imvu-antibot-list-actions">';
                    html += '<button type="button" class="imvu-antibot-remove-btn" data-user-id="' +
                        escapeHtml(item.userId) + '">Remove</button>';
                    html += '</span></li>';
                }
                html += '</ul>';
            }
            html += '</div>';
            return html;
        }

        function refreshPopup() {
            body.innerHTML = formatBootsPanel() + formatWhitelistPanel();
            var panels = body.getElementsByClassName('imvu-antibot-panel');
            var i;
            for (i = 0; i < panels.length; i++) {
                if (panels[i].getAttribute('data-panel') === activeTab) {
                    panels[i].className = 'imvu-antibot-panel';
                } else {
                    panels[i].className = 'imvu-antibot-panel hidden';
                }
            }
            bindPopupActions();
            if (open) {
                setPopupVisible(true);
                positionPopupNearButton();
            }
        }

        function refreshProtectionStatus() {
            var status = callImvu('getAntibotProtectionStatus');
            if (status) {
                onStatus(null, status);
            }
        }

        function applyWhitelistUpdate(result) {
            if (result && result.whitelist) {
                whitelist = result.whitelist;
            } else if (Array.isArray(result)) {
                whitelist = result;
            } else {
                whitelist = callImvu('getAntibotWhitelist') || whitelist;
            }
            refreshPopup();
        }

        function addWhitelistUser(userId, avatarName) {
            if (!userId) {
                return;
            }
            applyWhitelistUpdate(callImvu('addAntibotWhitelistUser', userId, avatarName || null));
        }

        function removeWhitelistUser(userId) {
            if (!userId) {
                return;
            }
            applyWhitelistUpdate(callImvu('removeAntibotWhitelistUser', userId));
        }

        function bindPopupActions() {
            var pageButtons = body.getElementsByClassName('imvu-antibot-page-btn');
            var i;
            for (i = 0; i < pageButtons.length; i++) {
                pageButtons[i].onclick = function (evt) {
                    var page = parseInt(this.getAttribute('data-page'), 10) || 0;
                    if (this.getAttribute('data-list') === 'whitelist') {
                        whitelistPage = page;
                    } else {
                        bootPage = page;
                    }
                    refreshPopup();
                    if (evt.stopPropagation) {
                        evt.stopPropagation();
                    }
                    return false;
                };
            }

            var addButtons = body.getElementsByClassName('imvu-antibot-whitelist-add-btn');
            for (i = 0; i < addButtons.length; i++) {
                addButtons[i].onclick = function (evt) {
                    addWhitelistUser(
                        this.getAttribute('data-user-id'),
                        this.getAttribute('data-user-name')
                    );
                    if (evt.stopPropagation) {
                        evt.stopPropagation();
                    }
                    return false;
                };
            }

            var trustButtons = body.getElementsByClassName('imvu-antibot-trust-btn');
            for (i = 0; i < trustButtons.length; i++) {
                trustButtons[i].onclick = function (evt) {
                    addWhitelistUser(this.getAttribute('data-user-id'), this.getAttribute('data-user-name'));
                    if (evt.stopPropagation) {
                        evt.stopPropagation();
                    }
                    return false;
                };
            }

            var removeButtons = body.getElementsByClassName('imvu-antibot-remove-btn');
            for (i = 0; i < removeButtons.length; i++) {
                removeButtons[i].onclick = function (evt) {
                    removeWhitelistUser(this.getAttribute('data-user-id'));
                    if (evt.stopPropagation) {
                        evt.stopPropagation();
                    }
                    return false;
                };
            }
        }

        function hidePopup() {
            open = false;
            setPopupVisible(false);
        }

        function showPopup() {
            open = true;
            bootPage = 0;
            whitelistPage = 0;
            setPopupVisible(true);
            refreshProtectionStatus();
            if (!whitelist.length) {
                whitelist = callImvu('getAntibotWhitelist') || [];
            }
            refreshPopup();
            positionPopupNearButton();
        }

        function onStatus(evt, info) {
            info = info || {};
            setActive(!!info.active);
            if (info.boots) {
                boots = info.boots;
            }
            if (info.whitelist) {
                whitelist = info.whitelist;
            }
            if (open) {
                refreshPopup();
            }
        }

        function onBoot(evt, info) {
            info = info || {};
            if (info.boots) {
                boots = info.boots;
            } else if (info.userId) {
                boots.push(info);
            }
            bootPage = 0;
            if (open) {
                refreshPopup();
            }
        }

        function nodeInAntibotPopup(node) {
            while (node) {
                if (node === popup || node === button) {
                    return true;
                }
                if (node.className && typeof node.className === 'string' &&
                        node.className.indexOf('imvu-antibot') !== -1) {
                    return true;
                }
                node = node.parentNode;
            }
            return false;
        }

        function closePopupIfOutside(evt) {
            if (!open) {
                return;
            }
            var target = evt.target || evt.srcElement;
            if (nodeInAntibotPopup(target)) {
                return;
            }
            hidePopup();
        }

        eventBus.registerInScope(
            'AntibotStatus',
            'SessionWindow.AntibotProtectionStatus',
            onStatus,
            'SessionWindow',
            textChatRoot
        );
        eventBus.registerInScope(
            'AntibotStatus',
            'SessionWindow.AntibotBooted',
            onBoot,
            'SessionWindow',
            textChatRoot
        );

        var j;
        for (j = 0; j < tabButtons.length; j++) {
            tabButtons[j].onclick = (function (tabBtn) {
                return function (evt) {
                    setTab(tabBtn.getAttribute('data-tab'));
                    if (evt.stopPropagation) {
                        evt.stopPropagation();
                    }
                    return false;
                };
            })(tabButtons[j]);
        }

        button.onclick = function (evt) {
            if (open) {
                hidePopup();
            } else {
                showPopup();
            }
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
            if (evt.preventDefault) {
                evt.preventDefault();
            }
            return false;
        };

        popup.getElementsByClassName('imvu-antibot-popup-close')[0].onclick = function (evt) {
            hidePopup();
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
            return false;
        };

        document.body.addEventListener('mousedown', closePopupIfOutside, true);

        popup.onmousedown = function (evt) {
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
        };

        textChatRoot.setAttribute(MARKER, '1');
        setTimeout(refreshProtectionStatus, 400);
        setTimeout(refreshProtectionStatus, 2000);
    }

    IMVU.Client.AntibotStatus = {
        attach: attach
    };

    function tryInit() {
        var root = document.getElementById('text-chat');
        if (!root || root.getAttribute(MARKER) === '1') {
            return;
        }
        if (window.IMVU && IMVU.Client && IMVU.Client.EventBus) {
            attach(root, IMVU.Client.EventBus);
            return;
        }
        setTimeout(tryInit, 150);
    }

    if (document.readyState === 'complete') {
        tryInit();
    } else if (window.addEventListener) {
        window.addEventListener('load', tryInit, false);
    } else {
        window.attachEvent('onload', tryInit);
    }
})();
