/* IMVU emoji picker — standalone button + overlay popup, cached Twemoji. */
(function () {
    if (!window.IMVU) {
        window.IMVU = {};
    }
    if (!IMVU.Client) {
        IMVU.Client = {};
    }
    if (IMVU.Client.ChatEmojiPicker) {
        return;
    }

    var cache = IMVU.Client.EmojiCache;
    var PICKER_MARKER = 'imvu-emoji-picker-installed';
    var PRELOAD_MARKER = 'imvu-emoji-preload-started';
    var REPO_URL = 'https://github.com/JSukar/IMVU-TOOLKIT';
    var OVERLAY_STYLE_ID = 'imvu-emoji-picker-overlay-css-v4';
    var FAVORITES_KEY = 'imvu_emoji_favorites';
    var FAVORITES_CATEGORY = 'favorites';

    function getPickerOverlayContext() {
        var overlayWin = window;
        var overlayDoc = document;
        try {
            if (window.parent && window.parent !== window && window.parent.document && window.parent.document.body) {
                overlayWin = window.parent;
                overlayDoc = window.parent.document;
            }
        } catch (e) {
        }
        return { win: overlayWin, doc: overlayDoc };
    }

    function frameViewportOffset() {
        var x = 0;
        var y = 0;
        try {
            if (window.frameElement && window.frameElement.getBoundingClientRect) {
                var frameRect = window.frameElement.getBoundingClientRect();
                x = frameRect.left;
                y = frameRect.top;
            }
        } catch (e) {
        }
        return { x: x, y: y };
    }

    function triggerRectInOverlay(trigger) {
        var rect = trigger.getBoundingClientRect ? trigger.getBoundingClientRect() : null;
        var off = frameViewportOffset();
        if (!rect) {
            return {
                top: (trigger.offsetTop || 0) + off.y,
                left: (trigger.offsetLeft || 0) + off.x,
                right: (trigger.offsetLeft || 0) + (trigger.offsetWidth || 34) + off.x,
                bottom: (trigger.offsetTop || 0) + (trigger.offsetHeight || 34) + off.y,
                width: trigger.offsetWidth || 34,
                height: trigger.offsetHeight || 34
            };
        }
        return {
            top: rect.top + off.y,
            left: rect.left + off.x,
            right: rect.right + off.x,
            bottom: rect.bottom + off.y,
            width: rect.width,
            height: rect.height
        };
    }

    function ensureOverlayStyles(overlayDoc) {
        if (!overlayDoc || overlayDoc.getElementById(OVERLAY_STYLE_ID)) {
            return;
        }
        var head = overlayDoc.getElementsByTagName('head')[0] || overlayDoc.documentElement;
        var style = overlayDoc.createElement('style');
        style.id = OVERLAY_STYLE_ID;
        style.type = 'text/css';
        style.appendChild(overlayDoc.createTextNode(
            '.imvu-emoji-picker{position:fixed;width:268px;background:#1a1a1a;border:1px solid #555;'
            + '-moz-border-radius:4px;-moz-box-shadow:0 2px 10px rgba(0,0,0,0.5);z-index:999999;overflow:visible}'
            + '.imvu-emoji-picker.hidden{display:none}'
            + '.imvu-emoji-picker-search-wrap{position:relative;padding:8px;border-bottom:1px solid #333;overflow:visible}'
            + '.imvu-emoji-picker-search{display:block;width:auto;height:28px;margin-right:92px;-moz-box-sizing:border-box;'
            + 'padding:5px 8px;border:1px solid #444;background:#111;color:#fff;font-size:12px;line-height:16px}'
            + '.imvu-emoji-picker-search.hint{color:#929292}'
            + '.imvu-emoji-picker-header-btns{position:absolute;right:8px;top:8px;width:88px;height:28px;'
            + 'line-height:28px;text-align:right;white-space:nowrap;z-index:5}'
            + '.imvu-emoji-picker-gear,.imvu-emoji-picker-info,.imvu-emoji-picker-fav-header{display:inline-block;width:26px;height:26px;margin:0 0 0 4px;'
            + 'padding:0;border:1px solid #444;background:#222;color:#bbb;text-align:center;cursor:pointer;'
            + '-moz-border-radius:13px;vertical-align:middle;overflow:hidden;-moz-user-select:none}'
            + '.imvu-emoji-picker-fav-header{font-family:Arial,sans-serif;font-size:14px;line-height:26px;'
            + 'padding-top:1px;color:#bbb}'
            + '.imvu-emoji-picker-fav-header.active,.imvu-emoji-picker-fav-header:hover{color:#f5c542;background:#333}'
            + '.imvu-emoji-picker-info{font-family:Georgia,"Times New Roman",serif;font-style:italic;font-weight:bold;'
            + 'font-size:13px;line-height:26px}'
            + '.imvu-emoji-picker-gear{font-family:Arial,sans-serif;font-size:14px;line-height:26px;padding-top:1px}'
            + '.imvu-emoji-picker-gear:hover,.imvu-emoji-picker-info:hover{background:#333;color:#fff}'
            + '.imvu-emoji-picker-settings{position:absolute;right:8px;top:48px;min-width:188px;padding:4px;'
            + 'border:1px solid #555;background:#1a1a1a;-moz-border-radius:4px;-moz-box-shadow:0 2px 8px rgba(0,0,0,0.45);z-index:1000000}'
            + '.imvu-emoji-picker-settings.hidden{display:none}'
            + '.imvu-emoji-picker-about{position:absolute;right:8px;top:48px;min-width:180px;padding:8px 10px;'
            + 'border:1px solid #555;background:#1a1a1a;-moz-border-radius:4px;-moz-box-shadow:0 2px 8px rgba(0,0,0,0.45);'
            + 'z-index:1000000;color:#ccc;font-size:11px;line-height:1.4}'
            + '.imvu-emoji-picker-about.hidden{display:none}'
            + '.imvu-emoji-picker-about a{color:#6eb5ff;text-decoration:underline}'
            + '.imvu-emoji-picker-about a:hover{color:#9ecdff}'
            + '.imvu-emoji-picker-settings-title{color:#888;font-size:9px;padding:2px 4px 4px;text-transform:uppercase}'
            + '.imvu-emoji-picker-settings-divider{border-top:1px solid #333;margin:4px 0 2px}'
            + '.imvu-emoji-picker-settings-mode{display:block;width:100%;margin:0 0 2px 0;padding:4px 6px;border:0;'
            + 'background:transparent;color:#ccc;font-size:10px;text-align:left;cursor:pointer;-moz-border-radius:3px}'
            + '.imvu-emoji-picker-settings-mode:hover{background:#333}'
            + '.imvu-emoji-picker-settings-mode.active{background:#444;color:#fff}'
            + '.imvu-emoji-picker-tabs{padding:4px 6px 3px;border-bottom:1px solid #333;white-space:nowrap;overflow-x:auto;'
            + 'overflow-y:hidden;height:28px;line-height:20px;background:#1a1a1a}'
            + '.imvu-emoji-picker-tab{display:inline-block;margin:0 2px 0 0;padding:2px 6px;border:0;background:transparent;'
            + 'color:#aaa;font-size:11px;cursor:pointer;-moz-border-radius:2px;line-height:18px}'
            + '.imvu-emoji-picker-tab.active{background:#333;color:#fff}'
            + '.imvu-emoji-picker-grid-wrap{height:240px;min-height:80px;overflow-y:auto;overflow-x:hidden;background:#1a1a1a;'
            + '-moz-border-radius:0 0 4px 4px}'
            + '.imvu-emoji-picker-grid{padding:4px;line-height:0}'
            + '.imvu-emoji-picker-cell{position:relative;display:inline-block;width:32px;height:32px;vertical-align:top}'
            + '.imvu-emoji-picker-item{width:28px;height:28px;margin:0;padding:2px;border:0;background:transparent;cursor:pointer;'
            + '-moz-border-radius:2px;display:inline-block;vertical-align:top;line-height:0;text-align:center}'
            + '.imvu-emoji-picker-item:hover{background:#333}'
            + '.imvu-emoji-picker-item img{width:28px;height:28px;border:0;vertical-align:middle}'
            + '.imvu-emoji-picker-item-fallback{display:inline-block;width:28px;height:28px;line-height:28px;font-size:16px;'
            + 'text-align:center;vertical-align:middle}'
            + '.imvu-emoji-picker-empty{color:#888;font-size:11px;padding:10px;text-align:center}'
            + '.imvu-emoji-picker-fav-toggle{position:absolute;right:0;top:0;width:14px;height:14px;margin:0;padding:0;border:0;'
            + 'line-height:14px;font-size:11px;color:#777;background:#1a1a1a;cursor:pointer;text-align:center;z-index:2}'
            + '.imvu-emoji-picker-fav-toggle.active,.imvu-emoji-picker-fav-toggle:hover{color:#f5c542}'
        ));
        head.appendChild(style);
    }

    function getStorageWindows() {
        var wins = [window];
        var seen = {};
        var i;
        seen[window] = true;
        try {
            if (window.parent && window.parent !== window && !seen[window.parent]) {
                wins.push(window.parent);
                seen[window.parent] = true;
            }
        } catch (e) {
        }
        try {
            if (window.top && window.top !== window && !seen[window.top]) {
                wins.push(window.top);
            }
        } catch (e) {
        }
        return wins;
    }

    var memoryFavoriteHexes = null;

    function syncFavoriteGlobals(hexes) {
        var wins = getStorageWindows();
        var i;
        var copy = hexes.slice(0);
        memoryFavoriteHexes = copy;
        for (i = 0; i < wins.length; i += 1) {
            try {
                wins[i].__IMVU_EMOJI_FAVORITES = copy;
            } catch (e) {
            }
        }
    }

    function readFavoriteHexesFromGlobals() {
        var wins = getStorageWindows();
        var i;
        var value;
        for (i = 0; i < wins.length; i += 1) {
            try {
                value = wins[i].__IMVU_EMOJI_FAVORITES;
                if (value && value.length) {
                    return value.slice(0);
                }
            } catch (e) {
            }
        }
        return null;
    }

    function readFavoriteHexesFromStorage() {
        var wins = getStorageWindows();
        var i;
        var raw;
        for (i = 0; i < wins.length; i += 1) {
            try {
                if (wins[i].localStorage) {
                    raw = wins[i].localStorage.getItem(FAVORITES_KEY);
                    if (raw !== null && raw !== undefined && raw !== '') {
                        return JSON.parse(raw);
                    }
                }
            } catch (e) {
            }
        }
        return null;
    }

    function loadFavoriteHexes() {
        var parsed;
        if (memoryFavoriteHexes !== null) {
            return memoryFavoriteHexes.slice(0);
        }
        try {
            parsed = readFavoriteHexesFromGlobals();
            if (parsed && parsed.length) {
                syncFavoriteGlobals(parsed);
                return parsed.slice(0);
            }
            parsed = readFavoriteHexesFromStorage();
            if (parsed !== null && parsed !== undefined) {
                syncFavoriteGlobals(parsed);
                return parsed.slice(0);
            }
        } catch (e) {
        }
        syncFavoriteGlobals([]);
        return [];
    }

    function saveFavoriteHexes(hexes) {
        var wins = getStorageWindows();
        var i;
        syncFavoriteGlobals(hexes);
        for (i = 0; i < wins.length; i += 1) {
            try {
                if (wins[i].localStorage) {
                    wins[i].localStorage.setItem(FAVORITES_KEY, JSON.stringify(hexes));
                    return;
                }
            } catch (e) {
            }
        }
    }

    function indexOfHex(hexes, hex) {
        var i;
        for (i = 0; i < hexes.length; i += 1) {
            if (hexes[i] === hex) {
                return i;
            }
        }
        return -1;
    }

    function buildHexEntryMap(categories) {
        var map = {};
        var i;
        var j;
        var cat;
        var entry;
        var hex;
        for (i = 0; i < categories.length; i += 1) {
            cat = categories[i];
            for (j = 0; j < cat.emojis.length; j += 1) {
                entry = cat.emojis[j];
                hex = cache.hexFromEmoji(entry.c);
                if (hex) {
                    map[hex] = entry;
                }
            }
        }
        return map;
    }

    function emojiHex(entry) {
        return cache.hexFromEmoji(entry.c);
    }

    function preloadEntries(entries) {
        cache.preloadEntries(entries);
    }

    function preloadCatalog(categories) {
        cache.preloadCatalog(categories);
    }

    function clearHint(input) {
        var hint = input.getAttribute('hint') || '';
        var cls = input.className || '';
        if (cls.indexOf('hint') !== -1 || (hint && input.value === hint)) {
            input.value = '';
            input.className = cls.replace(/\bhint\b/g, '').replace(/^\s+|\s+$/g, '');
        }
        if (window.jQuery) {
            window.jQuery(input).removeClass('hint');
        }
    }

    function insertAtCursor(input, text) {
        clearHint(input);
        var start;
        var end;
        var val;
        if (typeof input.selectionStart === 'number') {
            start = input.selectionStart;
            end = input.selectionEnd;
            val = input.value;
            input.value = val.substring(0, start) + text + val.substring(end);
            input.selectionStart = start + text.length;
            input.selectionEnd = start + text.length;
        } else if (document.selection && document.selection.createRange) {
            input.focus();
            document.selection.createRange().text = text;
        } else {
            input.value = (input.value || '') + text;
        }
        input.className = (input.className || '').replace(/\bhint\b/g, '').replace(/^\s+|\s+$/g, '');
        input.focus();
    }

    function matchesQuery(entry, query) {
        if (!query) {
            return true;
        }
        var haystack = (entry.n + ' ' + entry.k + ' ' + entry.c).toLowerCase();
        return haystack.indexOf(query) !== -1;
    }

    function isSecondaryClick(evt) {
        evt = evt || window.event;
        if (typeof evt.button === 'number') {
            return evt.button === 2;
        }
        if (typeof evt.which === 'number') {
            return evt.which === 3;
        }
        return false;
    }

    function flattenCategories(categories, query) {
        var flat = [];
        var i;
        var j;
        var cat;
        var entry;
        for (i = 0; i < categories.length; i += 1) {
            cat = categories[i];
            for (j = 0; j < cat.emojis.length; j += 1) {
                entry = cat.emojis[j];
                if (matchesQuery(entry, query)) {
                    flat.push(entry);
                }
            }
        }
        return flat;
    }

    function findInputRow(input) {
        var node = input;
        while (node) {
            if (node.id === 'inputRow') {
                return node;
            }
            node = node.parentNode;
        }
        return null;
    }

    function findSendButton(inputRow) {
        if (!inputRow) {
            return document.getElementById('send-button');
        }
        return inputRow.querySelector('#send-button') || document.getElementById('send-button');
    }

    function findPickerHost(textChatRoot) {
        return textChatRoot.querySelector('#input-row-wrapper')
            || textChatRoot.querySelector('#inputRow')
            || textChatRoot;
    }

    function getSuggestMode() {
        if (IMVU.Client.ChatEmojiSuggestions && IMVU.Client.ChatEmojiSuggestions.getMode) {
            return IMVU.Client.ChatEmojiSuggestions.getMode();
        }
        return 'replace';
    }

    function setSuggestMode(mode) {
        if (IMVU.Client.ChatEmojiSuggestions && IMVU.Client.ChatEmojiSuggestions.setMode) {
            IMVU.Client.ChatEmojiSuggestions.setMode(mode);
        }
        if (IMVU.Client.ChatEmojiSuggestions && IMVU.Client.ChatEmojiSuggestions.refreshUi) {
            IMVU.Client.ChatEmojiSuggestions.refreshUi();
        }
    }

    function getSuggestEnabled() {
        if (IMVU.Client.ChatEmojiSuggestions && IMVU.Client.ChatEmojiSuggestions.getEnabled) {
            return IMVU.Client.ChatEmojiSuggestions.getEnabled();
        }
        return true;
    }

    function setSuggestEnabled(enabled) {
        if (IMVU.Client.ChatEmojiSuggestions && IMVU.Client.ChatEmojiSuggestions.setEnabled) {
            IMVU.Client.ChatEmojiSuggestions.setEnabled(enabled);
        }
        if (IMVU.Client.ChatEmojiSuggestions && IMVU.Client.ChatEmojiSuggestions.refreshUi) {
            IMVU.Client.ChatEmojiSuggestions.refreshUi();
        }
    }

    var PICKER_GAP = 10;
    var MIN_GRID_HEIGHT = 120;
    var MAX_GRID_HEIGHT = 480;

    function getPickerChrome(picker, gridWrap) {
        gridWrap.style.height = '0px';
        var chrome = picker.offsetHeight;
        if (!chrome || chrome < 40) {
            chrome = 70;
        }
        return chrome;
    }

    function fitPickerGrid(picker, trigger, gridWrap, overlayWin) {
        var rect = triggerRectInOverlay(trigger);
        var chrome = getPickerChrome(picker, gridWrap);
        var spaceAbove = rect.top - PICKER_GAP - 4;
        var gridH = Math.min(MAX_GRID_HEIGHT, Math.max(MIN_GRID_HEIGHT, spaceAbove - chrome));

        gridWrap.style.height = gridH + 'px';
        return picker.offsetHeight;
    }

    function positionPickerFixed(picker, trigger, gridWrap, overlay) {
        var overlayWin = overlay.win;
        var pickerWidth = picker.offsetWidth || 268;
        var pickerHeight;
        var viewportW = overlayWin.innerWidth || overlayWin.document.documentElement.clientWidth || 800;
        var top;
        var left;
        var rect = triggerRectInOverlay(trigger);
        var bottomEdge;

        pickerHeight = fitPickerGrid(picker, trigger, gridWrap, overlayWin);
        bottomEdge = rect.top - PICKER_GAP;
        top = bottomEdge - pickerHeight;
        left = rect.right - pickerWidth;

        if (top < 4) {
            gridWrap.style.height = Math.max(MIN_GRID_HEIGHT, bottomEdge - 4 - getPickerChrome(picker, gridWrap)) + 'px';
            pickerHeight = picker.offsetHeight;
            top = bottomEdge - pickerHeight;
            if (top < 4) {
                top = 4;
            }
        }
        if (left < 4) {
            left = 4;
        }
        if (left + pickerWidth > viewportW - 4) {
            left = Math.max(4, viewportW - pickerWidth - 4);
        }

        picker.style.position = 'fixed';
        picker.style.top = top + 'px';
        picker.style.left = left + 'px';
        picker.style.right = 'auto';
        picker.style.bottom = 'auto';
        picker.style.marginBottom = '0';
    }

    function nodeInPickerTree(node, pickerEl, triggerEl, pickerDoc) {
        while (node) {
            if (node === pickerEl || node === triggerEl) {
                return true;
            }
            if (pickerDoc && node === pickerDoc) {
                return false;
            }
            node = node.parentNode;
        }
        return false;
    }

    function bindOutsideClose(overlay, chatDoc, pickerApi, button) {
        function closeIfOutside(evt) {
            if (!pickerApi.isOpen()) {
                return;
            }
            if (isSecondaryClick(evt)) {
                return;
            }
            var target = evt.target || evt.srcElement;
            if (nodeInPickerTree(target, pickerApi.element, button, null)) {
                return;
            }
            pickerApi.hide();
        }

        if (overlay.doc.addEventListener) {
            overlay.doc.addEventListener('mousedown', closeIfOutside, true);
        }
        if (chatDoc !== overlay.doc && chatDoc.addEventListener) {
            chatDoc.addEventListener('mousedown', closeIfOutside, true);
        }
    }

    function stopPickerEvent(evt) {
        if (evt.stopPropagation) {
            evt.stopPropagation();
        }
        if (evt.preventDefault) {
            evt.preventDefault();
        }
        return false;
    }

    function attachGridImgFallback(img) {
        var btn = img.parentNode;
        var hex;
        var emoji;
        var span;

        if (!btn || img.__imvuFallback) {
            return;
        }
        img.__imvuFallback = true;
        img.onload = function () {
            if (!this.width || !this.height || this.width < 8) {
                this.onerror();
            }
        };
        img.onerror = function () {
            if (this.__imvuFailed) {
                return;
            }
            hex = btn.getAttribute('data-emoji-hex');
            if (!hex && btn.parentNode && btn.parentNode.getAttribute) {
                hex = btn.parentNode.getAttribute('data-emoji-hex');
            }
            if (hex && this.src.indexOf('data:') === 0) {
                this.src = cache.cdnUrl(hex);
                return;
            }
            this.__imvuFailed = true;
            emoji = btn.getAttribute('data-emoji');
            this.style.display = 'none';
            span = document.createElement('span');
            span.className = 'imvu-emoji-picker-item-fallback';
            span.appendChild(document.createTextNode(emoji || '?'));
            btn.appendChild(span);
        };
    }

    function emojiCellHtml(entry, isFavorite) {
        var hex = emojiHex(entry);
        cache.persistHex(hex);
        return '<div class="imvu-emoji-picker-cell" data-emoji-hex="'
            + hex
            + '"><button type="button" class="imvu-emoji-picker-item" data-emoji="'
            + entry.c.replace(/"/g, '&quot;')
            + '" title="'
            + entry.n.replace(/"/g, '&quot;')
            + '"><img src="'
            + cache.getSrc(hex)
            + '" alt="" draggable="false"></button><button type="button" class="imvu-emoji-picker-fav-toggle'
            + (isFavorite ? ' active' : '')
            + '" title="'
            + (isFavorite ? 'Remove from favorites' : 'Add to favorites')
            + '">'
            + (isFavorite ? '\u2605' : '\u2606')
            + '</button></div>';
    }

    function createPicker(input, trigger, overlay) {
        ensureOverlayStyles(overlay.doc);

        var doc = overlay.doc;
        var picker = doc.createElement('div');
        picker.className = 'imvu-emoji-picker hidden';
        picker.id = 'imvu-emoji-picker';

        var searchWrap = doc.createElement('div');
        searchWrap.className = 'imvu-emoji-picker-search-wrap';

        var settings = doc.createElement('div');
        settings.className = 'imvu-emoji-picker-settings hidden';

        var settingsTitle = doc.createElement('div');
        settingsTitle.className = 'imvu-emoji-picker-settings-title';
        settingsTitle.appendChild(doc.createTextNode('Text shortcuts (LOL, :) )'));
        settings.appendChild(settingsTitle);

        var replaceBtn = doc.createElement('button');
        replaceBtn.type = 'button';
        replaceBtn.className = 'imvu-emoji-picker-settings-mode';
        replaceBtn.appendChild(doc.createTextNode('Replace word with emoji'));

        var appendBtn = doc.createElement('button');
        appendBtn.type = 'button';
        appendBtn.className = 'imvu-emoji-picker-settings-mode';
        appendBtn.appendChild(doc.createTextNode('Keep word, add emoji after'));

        settings.appendChild(replaceBtn);
        settings.appendChild(appendBtn);

        var suggestDivider = doc.createElement('div');
        suggestDivider.className = 'imvu-emoji-picker-settings-divider';

        var suggestTitle = doc.createElement('div');
        suggestTitle.className = 'imvu-emoji-picker-settings-title';
        suggestTitle.appendChild(doc.createTextNode('Recommendations'));

        var suggestOnBtn = doc.createElement('button');
        suggestOnBtn.type = 'button';
        suggestOnBtn.className = 'imvu-emoji-picker-settings-mode';
        suggestOnBtn.appendChild(doc.createTextNode('Show shortcut suggestions'));

        var suggestOffBtn = doc.createElement('button');
        suggestOffBtn.type = 'button';
        suggestOffBtn.className = 'imvu-emoji-picker-settings-mode';
        suggestOffBtn.appendChild(doc.createTextNode('Hide shortcut suggestions'));

        settings.appendChild(suggestDivider);
        settings.appendChild(suggestTitle);
        settings.appendChild(suggestOnBtn);
        settings.appendChild(suggestOffBtn);

        var gear = doc.createElement('button');
        gear.type = 'button';
        gear.className = 'imvu-emoji-picker-gear';
        gear.title = 'Shortcut settings';
        gear.appendChild(doc.createTextNode('\u2699'));

        var info = doc.createElement('button');
        info.type = 'button';
        info.className = 'imvu-emoji-picker-info';
        info.title = 'About this emoji picker';
        info.appendChild(doc.createTextNode('i'));

        var favHeader = doc.createElement('button');
        favHeader.type = 'button';
        favHeader.className = 'imvu-emoji-picker-fav-header';
        favHeader.title = 'Favorites';
        favHeader.appendChild(doc.createTextNode('\u2605'));

        var about = doc.createElement('div');
        about.className = 'imvu-emoji-picker-about hidden';
        about.innerHTML = 'This was made by J0<br><a href="'
            + REPO_URL
            + '" target="_blank">'
            + REPO_URL
            + '</a>';

        var search = doc.createElement('input');
        search.type = 'text';
        search.className = 'imvu-emoji-picker-search';
        search.setAttribute('hint', 'Search...');

        var headerBtns = doc.createElement('div');
        headerBtns.className = 'imvu-emoji-picker-header-btns';
        headerBtns.appendChild(favHeader);
        headerBtns.appendChild(info);
        headerBtns.appendChild(gear);

        searchWrap.appendChild(search);
        searchWrap.appendChild(headerBtns);

        var tabs = doc.createElement('div');
        tabs.className = 'imvu-emoji-picker-tabs';

        var gridWrap = doc.createElement('div');
        gridWrap.className = 'imvu-emoji-picker-grid-wrap';
        var grid = doc.createElement('div');
        grid.className = 'imvu-emoji-picker-grid';
        gridWrap.appendChild(grid);

        picker.appendChild(searchWrap);
        picker.appendChild(tabs);
        picker.appendChild(gridWrap);
        picker.appendChild(settings);
        picker.appendChild(about);
        doc.body.appendChild(picker);

        var categories = window.IMVU_EMOJI_CATEGORIES || [];
        var hexEntryMap = buildHexEntryMap(categories);
        var favoriteSet = {};
        var activeCategory = categories.length ? categories[0].id : '';
        var open = false;
        var settingsOpen = false;
        var aboutOpen = false;

        function refreshFavoriteSet() {
            var hexes = loadFavoriteHexes();
            var next = {};
            var i;
            for (i = 0; i < hexes.length; i += 1) {
                next[hexes[i]] = true;
            }
            favoriteSet = next;
        }

        function isFavoriteHex(hex) {
            return !!favoriteSet[hex];
        }

        function toggleFavoriteHex(hex) {
            var hexes = loadFavoriteHexes();
            var idx = indexOfHex(hexes, hex);
            if (idx === -1) {
                hexes.push(hex);
            } else {
                hexes.splice(idx, 1);
            }
            saveFavoriteHexes(hexes);
            refreshFavoriteSet();
        }

        function updateHeaderFavBtn() {
            favHeader.className = 'imvu-emoji-picker-fav-header'
                + (activeCategory === FAVORITES_CATEGORY ? ' active' : '');
        }

        function showFavoritesTab() {
            hideAbout();
            hideSettings();
            activeCategory = FAVORITES_CATEGORY;
            search.value = '';
            renderTabs();
            renderGrid();
            updateHeaderFavBtn();
        }

        function getFavoriteEntries() {
            var hexes = loadFavoriteHexes();
            var entries = [];
            var i;
            var entry;
            for (i = 0; i < hexes.length; i += 1) {
                entry = hexEntryMap[hexes[i]];
                if (entry) {
                    entries.push(entry);
                }
            }
            return entries;
        }

        refreshFavoriteSet();

        function hideAbout() {
            about.className = 'imvu-emoji-picker-about hidden';
            aboutOpen = false;
        }

        function hideSettings() {
            settings.className = 'imvu-emoji-picker-settings hidden';
            settingsOpen = false;
        }

        function updateSettingsUi() {
            var mode = getSuggestMode();
            var enabled = getSuggestEnabled();
            replaceBtn.className = 'imvu-emoji-picker-settings-mode'
                + (mode === 'replace' ? ' active' : '');
            appendBtn.className = 'imvu-emoji-picker-settings-mode'
                + (mode === 'append' ? ' active' : '');
            suggestOnBtn.className = 'imvu-emoji-picker-settings-mode'
                + (enabled ? ' active' : '');
            suggestOffBtn.className = 'imvu-emoji-picker-settings-mode'
                + (!enabled ? ' active' : '');
        }

        function toggleSettings() {
            hideAbout();
            if (settingsOpen) {
                hideSettings();
            } else {
                updateSettingsUi();
                settings.className = 'imvu-emoji-picker-settings';
                settingsOpen = true;
            }
        }

        function toggleAbout() {
            hideSettings();
            if (aboutOpen) {
                hideAbout();
            } else {
                about.className = 'imvu-emoji-picker-about';
                aboutOpen = true;
            }
        }

        function renderTabs() {
            var html = [];
            var i;
            var cat;
            for (i = 0; i < categories.length; i += 1) {
                cat = categories[i];
                html.push(
                    '<button type="button" class="imvu-emoji-picker-tab'
                    + (cat.id === activeCategory ? ' active' : '')
                    + '" data-category="'
                    + cat.id
                    + '" title="'
                    + cat.label.replace(/"/g, '&quot;')
                    + '">'
                    + cat.label
                    + '</button>'
                );
            }
            tabs.innerHTML = html.join('');
            updateHeaderFavBtn();
        }

        function renderGrid() {
            var query = String(search.value || '').toLowerCase();
            var hint = search.getAttribute('hint') || '';
            if (search.className.indexOf('hint') !== -1 && search.value === hint) {
                query = '';
            }
            var html = [];
            var i;
            var j;
            var cat;
            var entries;

            if (query) {
                entries = flattenCategories(categories, query);
                for (i = 0; i < entries.length; i += 1) {
                    html.push(emojiCellHtml(entries[i], isFavoriteHex(emojiHex(entries[i]))));
                }
            } else if (activeCategory === FAVORITES_CATEGORY) {
                entries = getFavoriteEntries();
                preloadEntries(entries);
                for (i = 0; i < entries.length; i += 1) {
                    html.push(emojiCellHtml(entries[i], true));
                }
            } else {
                for (i = 0; i < categories.length; i += 1) {
                    cat = categories[i];
                    if (cat.id !== activeCategory) {
                        continue;
                    }
                    preloadEntries(cat.emojis);
                    for (j = 0; j < cat.emojis.length; j += 1) {
                        html.push(emojiCellHtml(
                            cat.emojis[j],
                            isFavoriteHex(emojiHex(cat.emojis[j]))
                        ));
                    }
                    break;
                }
            }

            if (!html.length) {
                if (activeCategory === FAVORITES_CATEGORY && !query) {
                    grid.innerHTML = '<div class="imvu-emoji-picker-empty">No favorites yet.<br>Click &#9734; on any emoji to add it.</div>';
                } else {
                    grid.innerHTML = '<div class="imvu-emoji-picker-empty">No emoji found</div>';
                }
            } else {
                grid.innerHTML = html.join('');
                var imgs = grid.getElementsByTagName('img');
                var k;
                var btn;
                var cell;
                var hex;
                for (k = 0; k < imgs.length; k += 1) {
                    btn = imgs[k].parentNode;
                    cell = btn ? btn.parentNode : null;
                    hex = cell && cell.getAttribute ? cell.getAttribute('data-emoji-hex') : null;
                    if (btn && hex) {
                        attachGridImgFallback(imgs[k]);
                        cache.upgradeImg(imgs[k], hex);
                    }
                }
            }
        }

        function showPicker() {
            hideSettings();
            hideAbout();
            renderTabs();
            renderGrid();
            picker.className = 'imvu-emoji-picker';
            picker.style.visibility = 'visible';
            picker.style.left = '-10000px';
            picker.style.top = '0';
            positionPickerFixed(picker, trigger, gridWrap, overlay);
            open = true;
            clearHint(search);
            search.focus();
        }

        function hidePicker() {
            picker.className = 'imvu-emoji-picker hidden';
            open = false;
            hideSettings();
            hideAbout();
            search.value = '';
            search.className = (search.className || '').replace(/\bhint\b/g, '').replace(/^\s+|\s+$/g, '');
        }

        replaceBtn.onclick = function (evt) {
            setSuggestMode('replace');
            updateSettingsUi();
            hideSettings();
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
        };

        appendBtn.onclick = function (evt) {
            setSuggestMode('append');
            updateSettingsUi();
            hideSettings();
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
        };

        suggestOnBtn.onclick = function (evt) {
            setSuggestEnabled(true);
            updateSettingsUi();
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
        };

        suggestOffBtn.onclick = function (evt) {
            setSuggestEnabled(false);
            updateSettingsUi();
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
        };

        favHeader.onmousedown = function (evt) {
            showFavoritesTab();
            return stopPickerEvent(evt);
        };

        favHeader.onclick = function (evt) {
            return stopPickerEvent(evt);
        };

        gear.onmousedown = function (evt) {
            toggleSettings();
            return stopPickerEvent(evt);
        };

        info.onmousedown = function (evt) {
            toggleAbout();
            return stopPickerEvent(evt);
        };

        gear.onclick = function (evt) {
            return stopPickerEvent(evt);
        };

        info.onclick = function (evt) {
            return stopPickerEvent(evt);
        };

        settings.onclick = function (evt) {
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
        };

        settings.onmousedown = function (evt) {
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
        };

        about.onmousedown = function (evt) {
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
        };

        search.onkeydown = function (evt) {
            evt = evt || window.event;
            if (evt.keyCode === 27) {
                hidePicker();
                if (evt.stopPropagation) {
                    evt.stopPropagation();
                }
                return false;
            }
            if (evt.keyCode === 13) {
                if (evt.preventDefault) {
                    evt.preventDefault();
                }
                return false;
            }
        };

        search.onkeyup = function () {
            renderGrid();
        };

        search.onfocus = function () {
            clearHint(search);
        };

        tabs.onclick = function (evt) {
            var target = evt.target || evt.srcElement;
            var tab = target;
            while (tab && tab !== tabs) {
                if (tab.className && tab.className.indexOf('imvu-emoji-picker-tab') !== -1) {
                    activeCategory = tab.getAttribute('data-category') || activeCategory;
                    search.value = '';
                    renderTabs();
                    renderGrid();
                    if (evt.stopPropagation) {
                        evt.stopPropagation();
                    }
                    return;
                }
                tab = tab.parentNode;
            }
        };

        function findGridCell(target) {
            var node = target;
            while (node && node !== grid) {
                if (node.className && node.className.indexOf('imvu-emoji-picker-cell') !== -1) {
                    return node;
                }
                node = node.parentNode;
            }
            return null;
        }

        function findFavToggleButton(target) {
            var node = target;
            while (node && node !== grid) {
                if (node.className && node.className.indexOf('imvu-emoji-picker-fav-toggle') !== -1) {
                    return node;
                }
                node = node.parentNode;
            }
            return null;
        }

        function findGridEmojiButton(target) {
            var node = target;
            while (node && node !== grid) {
                if (node.className && node.className.indexOf('imvu-emoji-picker-item') !== -1) {
                    return node;
                }
                node = node.parentNode;
            }
            return null;
        }

        function toggleFavoriteFromEvent(evt) {
            var target = evt.target || evt.srcElement;
            var cell = findGridCell(target);
            var hex;
            if (!cell) {
                return false;
            }
            hex = cell.getAttribute('data-emoji-hex');
            if (!hex) {
                return false;
            }
            toggleFavoriteHex(hex);
            renderGrid();
            updateHeaderFavBtn();
            if (evt.preventDefault) {
                evt.preventDefault();
            }
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
            return true;
        }

        function handleGridActivate(evt) {
            var target = evt.target || evt.srcElement;
            if (findFavToggleButton(target)) {
                toggleFavoriteFromEvent(evt);
                return;
            }
            var button = findGridEmojiButton(target);
            if (!button) {
                return;
            }
            var emoji = button.getAttribute('data-emoji');
            if (emoji) {
                insertAtCursor(input, emoji);
            }
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
        }

        grid.onclick = handleGridActivate;

        if (window.IMVU && IMVU.Client && IMVU.Client.util && IMVU.Client.util.hint) {
            IMVU.Client.util.hint([search]);
        }

        cache.persistHex('1f60a');

        return {
            toggle: function () {
                if (open) {
                    hidePicker();
                } else {
                    showPicker();
                }
            },
            hide: hidePicker,
            isOpen: function () { return open; },
            element: picker,
            trigger: trigger
        };
    }

    function attach(textChatRoot) {
        if (!textChatRoot || textChatRoot.getAttribute(PICKER_MARKER) === '1') {
            return;
        }

        var input = textChatRoot.querySelector('input');
        var inputRow = findInputRow(input);
        var sendButton = findSendButton(inputRow);
        var pickerHost = findPickerHost(textChatRoot);
        if (!input || !inputRow || !sendButton || !pickerHost) {
            return;
        }

        var hostCls = pickerHost.className || '';
        if (hostCls.indexOf('imvu-emoji-picker-host') === -1) {
            pickerHost.className = (hostCls + ' imvu-emoji-picker-host').replace(/^\s+|\s+$/g, '');
        }
        var rootCls = textChatRoot.className || '';
        if (rootCls.indexOf('imvu-emoji-picker-root') === -1) {
            textChatRoot.className = (rootCls + ' imvu-emoji-picker-root').replace(/^\s+|\s+$/g, '');
        }

        var button = document.createElement('button');
        button.type = 'button';
        button.id = 'emoji-button';
        button.className = 'imvu-emoji-button';
        button.title = 'Emoji';
        button.innerHTML = '<img src="' + cache.getSrc('1f60a') + '" alt="" draggable="false">';
        cache.upgradeImg(button.getElementsByTagName('img')[0], '1f60a');
        inputRow.insertBefore(button, sendButton);

        var overlay = getPickerOverlayContext();
        var pickerApi = createPicker(input, button, overlay);

        button.onclick = function (evt) {
            pickerApi.toggle();
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
            if (evt.preventDefault) {
                evt.preventDefault();
            }
            return false;
        };

        bindOutsideClose(overlay, document, pickerApi, button);

        if (!window[PRELOAD_MARKER]) {
            window[PRELOAD_MARKER] = true;
            preloadCatalog(window.IMVU_EMOJI_CATEGORIES || []);
        }

        textChatRoot.setAttribute(PICKER_MARKER, '1');
    }

    IMVU.Client.ChatEmojiPicker = {
        attach: attach,
        preload: preloadCatalog
    };

    function tryInit() {
        var root = document.getElementById('text-chat');
        if (root && root.querySelector('input') && window.IMVU_EMOJI_CATEGORIES) {
            if (window.IMVU && IMVU.Client && IMVU.Client.ChatTool) {
                attach(root);
                return;
            }
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
