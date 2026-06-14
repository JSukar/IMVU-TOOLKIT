/* IMVU emoji cache — persist Twemoji PNGs in localStorage after verified CDN fetch. */
(function () {
    if (!window.IMVU) {
        window.IMVU = {};
    }
    if (!IMVU.Client) {
        IMVU.Client = {};
    }
    if (IMVU.Client.EmojiCache) {
        return;
    }

    var TWEMOJI_BASE = 'https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/72x72/';
    var STORAGE_PREFIX = 'imvu_emoji_v1_';
    var memory = {};
    var persistStarted = {};
    var failedHex = {};

    function readStorage(hex) {
        try {
            if (window.localStorage) {
                return localStorage.getItem(STORAGE_PREFIX + hex);
            }
        } catch (e) {
        }
        return null;
    }

    function writeStorage(hex, dataUrl) {
        try {
            if (window.localStorage) {
                localStorage.setItem(STORAGE_PREFIX + hex, dataUrl);
            }
        } catch (e) {
        }
    }

    function removeStorage(hex) {
        try {
            if (window.localStorage) {
                localStorage.removeItem(STORAGE_PREFIX + hex);
            }
        } catch (e) {
        }
    }

    function isValidDataUrl(value) {
        return value && value.indexOf('data:image/') === 0 && value.length > 120;
    }

    function normalizeEmojiStr(value) {
        if (value === null || value === undefined) {
            return '';
        }
        if (typeof value === 'string') {
            return value;
        }
        if (typeof value === 'object' && value.c !== null && value.c !== undefined) {
            return normalizeEmojiStr(value.c);
        }
        return String(value);
    }

    function hexFromEmoji(emojiStr) {
        var parts = [];
        var i = 0;
        emojiStr = normalizeEmojiStr(emojiStr);
        if (!emojiStr) {
            return '';
        }
        while (i < emojiStr.length) {
            var c = emojiStr.charCodeAt(i);
            if (c >= 0xD800 && c <= 0xDBFF && i + 1 < emojiStr.length) {
                var c2 = emojiStr.charCodeAt(i + 1);
                if (c2 >= 0xDC00 && c2 <= 0xDFFF) {
                    var cp = ((c - 0xD800) << 10) + (c2 - 0xDC00) + 0x10000;
                    if (cp !== 0xFE0F) {
                        parts.push(cp.toString(16));
                    }
                    i += 2;
                    continue;
                }
            }
            if (c === 0xFE0F) {
                i += 1;
                continue;
            }
            if (c === 0x200D) {
                parts.push('200d');
                i += 1;
                continue;
            }
            parts.push(c.toString(16));
            i += 1;
        }
        return parts.join('-');
    }

    function cdnUrl(hex) {
        return TWEMOJI_BASE + hex + '.png';
    }

    function getSrc(hex) {
        if (failedHex[hex]) {
            return cdnUrl(hex);
        }
        if (memory[hex]) {
            return memory[hex];
        }
        var stored = readStorage(hex);
        if (stored && isValidDataUrl(stored)) {
            memory[hex] = stored;
            return stored;
        }
        if (stored) {
            removeStorage(hex);
        }
        return cdnUrl(hex);
    }

    function verifyUrlOk(url, cb) {
        var xhr;
        try {
            xhr = new XMLHttpRequest();
        } catch (e) {
            cb(true);
            return;
        }
        xhr.open('GET', url, true);
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                cb(xhr.status === 200 || xhr.status === 0);
            }
        };
        xhr.onerror = function () {
            cb(false);
        };
        try {
            xhr.send(null);
        } catch (e2) {
            cb(true);
        }
    }

    function cacheImageData(hex, url, img, cb) {
        var canvas;
        var ctx;
        var data;

        if (!img || !img.width || !img.height || img.width < 8 || img.height < 8) {
            failedHex[hex] = true;
            memory[hex] = url;
            if (cb) {
                cb(false);
            }
            return;
        }

        try {
            canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.drawImage(img, 0, 0);
                data = canvas.toDataURL('image/png');
                if (isValidDataUrl(data)) {
                    memory[hex] = data;
                    writeStorage(hex, data);
                    if (cb) {
                        cb(true);
                    }
                    return;
                }
            }
        } catch (e) {
        }

        memory[hex] = url;
        if (cb) {
            cb(false);
        }
    }

    function loadImageToCache(hex, url, cb) {
        var img = new Image();

        if (img.crossOrigin !== undefined) {
            img.crossOrigin = 'Anonymous';
        }

        img.onload = function () {
            cacheImageData(hex, url, img, cb);
        };
        img.onerror = function () {
            failedHex[hex] = true;
            memory[hex] = url;
            if (cb) {
                cb(false);
            }
        };
        img.src = url;
    }

    function persistHex(hex, cb) {
        var cached;
        var stored;
        var url;

        if (!hex) {
            if (cb) {
                cb(false);
            }
            return;
        }

        if (failedHex[hex]) {
            if (cb) {
                cb(false);
            }
            return;
        }

        if (persistStarted[hex]) {
            if (cb) {
                cb(true);
            }
            return;
        }

        cached = memory[hex];
        if (cached && isValidDataUrl(cached)) {
            if (cb) {
                cb(true);
            }
            return;
        }

        stored = readStorage(hex);
        if (stored && isValidDataUrl(stored)) {
            memory[hex] = stored;
            if (cb) {
                cb(true);
            }
            return;
        }
        if (stored) {
            removeStorage(hex);
        }

        persistStarted[hex] = true;
        url = cdnUrl(hex);

        verifyUrlOk(url, function (ok) {
            if (!ok) {
                failedHex[hex] = true;
                memory[hex] = url;
                persistStarted[hex] = false;
                if (cb) {
                    cb(false);
                }
                return;
            }

            loadImageToCache(hex, url, function (success) {
                persistStarted[hex] = false;
                if (cb) {
                    cb(success);
                }
            });
        });
    }

    function preloadEntries(entries) {
        var i;
        var entry;
        var emoji;
        if (!entries || !entries.length) {
            return;
        }
        for (i = 0; i < entries.length; i += 1) {
            entry = entries[i];
            if (!entry) {
                continue;
            }
            emoji = entry.c !== null && entry.c !== undefined ? entry.c : entry;
            persistHex(hexFromEmoji(emoji));
        }
    }

    function preloadCatalog(categories) {
        var cat;
        var emojis;
        if (!categories || !categories.length) {
            return;
        }
        cat = categories[0];
        if (!cat) {
            return;
        }
        emojis = cat.emojis;
        if (emojis && emojis.length) {
            preloadEntries(emojis);
        }
    }

    function upgradeImg(img, hex) {
        if (!img || !hex) {
            return;
        }

        persistHex(hex, function () {
            var src = getSrc(hex);
            if (img.src !== src) {
                img.src = src;
            }
        });
    }

    IMVU.Client.EmojiCache = {
        base: TWEMOJI_BASE,
        hexFromEmoji: hexFromEmoji,
        cdnUrl: cdnUrl,
        getSrc: getSrc,
        persistHex: persistHex,
        preloadEntries: preloadEntries,
        preloadCatalog: preloadCatalog,
        upgradeImg: upgradeImg
    };
})();
