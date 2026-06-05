/* IMVU emoji display patch — Gecko 1.9 cannot paint color emoji fonts; use Twemoji images. */
(function () {
    if (!window.IMVU) {
        window.IMVU = {};
    }
    if (!IMVU.Client) {
        IMVU.Client = {};
    }
    if (!IMVU.Client.util) {
        IMVU.Client.util = {};
    }
    if (IMVU.Client.util.linkifyWithEmoji) {
        return;
    }

    var TWEMOJI_BASE = 'https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/72x72/';
    var EMOJI_CDN_FALLBACK = 'https://emojicdn.elk.sh/';

    // Split on emoji runs (surrogate pairs, flags, BMP symbols).
    var EMOJI_SPLIT_RE = /(\uD83C[\uDFFB-\uDFFF]|\uD83C[\uDDE6-\uDDFF]{2}|[\uD800-\uDBFF][\uDC00-\uDFFF]+|[\u2600-\u27BF][\uFE0F]?|[\u2300-\u23FF])/g;
    var EMOJI_TEST_RE = /^(\uD83C[\uDFFB-\uDFFF]|\uD83C[\uDDE6-\uDDFF]{2}|[\uD800-\uDBFF][\uDC00-\uDFFF]+|[\u2600-\u27BF][\uFE0F]?|[\u2300-\u23FF])$/;

    function isEmojiSegment(segment) {
        return segment && EMOJI_TEST_RE.test(segment);
    }

    function codePointsToTwemojiHex(emojiStr) {
        var parts = [];
        var i = 0;
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

    function emojiImageElement(emojiStr) {
        var cache = IMVU.Client.EmojiCache;
        var hex = cache ? cache.hexFromEmoji(emojiStr) : codePointsToTwemojiHex(emojiStr);
        var img = document.createElement('img');
        img.className = 'emoji-inline';
        img.alt = emojiStr;
        img.title = emojiStr;
        img.src = cache ? cache.getSrc(hex) : (TWEMOJI_BASE + hex + '.png');
        img.setAttribute('draggable', 'false');
        if (cache) {
            cache.upgradeImg(img, hex);
        }
        img.onerror = function () {
            if (!this.__emojiFallback) {
                this.__emojiFallback = true;
                this.src = EMOJI_CDN_FALLBACK + hex + '?style=twitter';
                return;
            }
            this.style.display = 'none';
            var span = document.createElement('span');
            span.className = 'emoji-fallback-char';
            span.appendChild(document.createTextNode(emojiStr));
            if (this.parentNode) {
                this.parentNode.replaceChild(span, this);
            }
        };
        return img;
    }

    IMVU.Client.util.linkifyWithEmoji = function (text) {
        var elements = [];
        if (!text) {
            return elements;
        }

        var parts = String(text).split(EMOJI_SPLIT_RE);
        var i;
        for (i = 0; i < parts.length; i += 1) {
            var part = parts[i];
            if (!part) {
                continue;
            }
            if (isEmojiSegment(part)) {
                elements.push(emojiImageElement(part));
            } else {
                var linked = IMVU.Client.util.linkify(part);
                var j;
                for (j = 0; j < linked.length; j += 1) {
                    elements.push(linked[j]);
                }
            }
        }
        return elements;
    };
})();
