/* IMVU emoji text shortcuts — iMessage-style LOL → 😂 suggestions. */
(function () {
    if (!window.IMVU) {
        window.IMVU = {};
    }
    if (!IMVU.Client) {
        IMVU.Client = {};
    }
    if (IMVU.Client.ChatEmojiSuggestions) {
        return;
    }

    var cache = IMVU.Client.EmojiCache;
    var MARKER = 'imvu-emoji-suggest-installed';
    var MODE_KEY = 'imvu_emoji_suggest_mode';
    var ENABLED_KEY = 'imvu_emoji_suggest_enabled';
    var MODE_REPLACE = 'replace';
    var MODE_APPEND = 'append';
    var runtimeMode = null;
    var runtimeEnabled = null;

    if (!window.IMVU_EMOJI_SHORTCUTS) {
        window.IMVU_EMOJI_SHORTCUTS = {
            lol: '\uD83D\uDE02',
            lmao: '\uD83D\uDE02',
            lmfaoo: '\uD83D\uDE02',
            rofl: '\uD83D\uDE02',
            haha: '\uD83D\uDE02',
            hahaha: '\uD83D\uDE02',
            hehe: '\uD83D\uDE02',
            lolz: '\uD83D\uDE02',
            omg: '\uD83D\uDE32',
            omfg: '\uD83D\uDE32',
            wow: '\uD83D\uDE2E',
            wtf: '\uD83D\uDE33',
            yay: '\uD83C\uDF89',
            yayy: '\uD83C\uDF89',
            woo: '\uD83C\uDF89',
            yesss: '\uD83D\uDC4D',
            nooo: '\uD83D\uDE22',
            cool: '\uD83D\uDE0E',
            nice: '\uD83D\uDC4D',
            gg: '\uD83D\uDC4D',
            ggs: '\uD83D\uDC4D',
            wp: '\uD83D\uDC4F',
            ty: '\uD83D\uDE4F',
            thx: '\uD83D\uDE4F',
            thanks: '\uD83D\uDE4F',
            thankyou: '\uD83D\uDE4F',
            please: '\uD83D\uDE4F',
            pls: '\uD83D\uDE4F',
            sorry: '\uD83D\uDE14',
            sry: '\uD83D\uDE14',
            welcome: '\uD83D\uDC4B',
            wb: '\uD83D\uDC4B',
            congrats: '\uD83C\uDF89',
            grats: '\uD83C\uDF89',
            love: '\u2764',
            heart: '\u2764',
            hearts: '\uD83D\uDC95',
            fire: '\uD83D\uDD25',
            lit: '\uD83D\uDD25',
            hot: '\uD83D\uDD25',
            '100': '\uD83D\uDCAF',
            ok: '\uD83D\uDC4C',
            okay: '\uD83D\uDC4C',
            yes: '\uD83D\uDC4D',
            yeah: '\uD83D\uDC4D',
            yep: '\uD83D\uDC4D',
            yup: '\uD83D\uDC4D',
            no: '\uD83D\uDC4E',
            nope: '\uD83D\uDC4E',
            nah: '\uD83D\uDC4E',
            angry: '\uD83D\uDE20',
            mad: '\uD83D\uDE20',
            sad: '\uD83D\uDE22',
            cry: '\uD83D\uDE22',
            crying: '\uD83D\uDE2D',
            sleepy: '\uD83D\uDE34',
            sleep: '\uD83D\uDE34',
            tired: '\uD83D\uDE34',
            party: '\uD83C\uDF89',
            beer: '\uD83C\uDF7A',
            wine: '\uD83C\uDF77',
            pizza: '\uD83C\uDF55',
            burger: '\uD83C\uDF54',
            fries: '\uD83C\uDF5F',
            taco: '\uD83C\uDF2E',
            coffee: '\u2615',
            tea: '\uD83C\uDF75',
            cake: '\uD83C\uDF82',
            cookie: '\uD83C\uDF6A',
            yum: '\uD83D\uDE0B',
            hungry: '\uD83D\uDE0B',
            music: '\uD83C\uDFB5',
            star: '\u2B50',
            sparkle: '\u2728',
            shrug: '\uD83E\uDD37',
            think: '\uD83E\uDD14',
            thinking: '\uD83E\uDD14',
            clap: '\uD83D\uDC4F',
            wave: '\uD83D\uDC4B',
            hi: '\uD83D\uDC4B',
            hello: '\uD83D\uDC4B',
            hey: '\uD83D\uDC4B',
            sup: '\uD83D\uDC4B',
            bye: '\uD83D\uDC4B',
            cya: '\uD83D\uDC4B',
            gn: '\uD83D\uDE34',
            gm: '\uD83C\uDF1E',
            goodnight: '\uD83D\uDE34',
            goodmorning: '\uD83C\uDF1E',
            brb: '\uD83D\uDEAA',
            gtg: '\uD83D\uDEAA',
            kiss: '\uD83D\uDE18',
            xoxo: '\uD83D\uDC8B',
            poop: '\uD83D\uDCA9',
            skull: '\uD83D\uDC80',
            dead: '\uD83D\uDC80',
            rip: '\uD83D\uDC80',
            f: '\uD83D\uDE14',
            eyes: '\uD83D\uDC40',
            sus: '\uD83D\uDC40',
            money: '\uD83D\uDCB0',
            cash: '\uD83D\uDCB0',
            rich: '\uD83D\uDCB0',
            sun: '\u2600',
            moon: '\uD83C\uDF19',
            rain: '\uD83C\uDF27',
            snow: '\u2744',
            cloud: '\u2601',
            rainbow: '\uD83C\uDF08',
            dog: '\uD83D\uDC36',
            cat: '\uD83D\uDC31',
            aww: '\uD83E\uDD7A',
            cute: '\uD83E\uDD7A',
            wink: '\uD83D\uDE09',
            blush: '\uD83D\uDE0A',
            bro: '\uD83E\uDD1D',
            sis: '\uD83D\uDC96',
            fam: '\uD83D\uDC68\uD83D\uDC69\uD83D\uDC67\uD83D\uDC66',
            bet: '\uD83D\uDC4D',
            facts: '\uD83D\uDCAF',
            mood: '\uD83D\uDE0C',
            vibe: '\uD83D\uDE0E',
            slay: '\uD83D\uDC85',
            queen: '\uD83D\uDC51',
            king: '\uD83D\uDC51',
            crown: '\uD83D\uDC51',
            cap: '\uD83E\uDDE2',
            gossip: '\uD83D\uDC40',
            spooky: '\uD83D\uDC7B',
            boo: '\uD83D\uDC7B',
            ghost: '\uD83D\uDC7B',
            xmas: '\uD83C\uDF84',
            halloween: '\uD83C\uDF83',
            rose: '\uD83C\uDF39',
            flower: '\uD83C\uDF38',
            tree: '\uD83C\uDF33',
            ocean: '\uD83C\uDF0A',
            beach: '\uD83C\uDFD6',
            plane: '\u2708',
            car: '\uD83D\uDE97',
            game: '\uD83C\uDFAE',
            win: '\uD83C\uDFC6',
            lose: '\uD83D\uDE14',
            help: '\uD83D\uDEA8',
            stop: '\uD83D\uDED1',
            wait: '\u270B',
            run: '\uD83C\uDFC3',
            oof: '\uD83D\uDE30',
            ugh: '\uD83D\uDE12',
            meh: '\uD83D\uDE10',
            ew: '\uD83E\uDD22',
            sick: '\uD83E\uDD12',
            cold: '\uD83E\uDD76',
            devil: '\uD83D\uDE08',
            angel: '\uD83D\uDE07',
            alien: '\uD83D\uDC7D',
            robot: '\uD83E\uDD16',
            unicorn: '\uD83E\uDD84',
            chicken: '\uD83D\uDC14',
            monkey: '\uD83D\uDC12',
            bear: '\uD83D\uDC3B',
            panda: '\uD83D\uDC3C',
            lion: '\uD83D\uDC81',
            tiger: '\uD83D\uDC2F',
            fish: '\uD83D\uDC1F',
            bird: '\uD83D\uDC26',
            idk: '\uD83E\uDD37',
            ik: '\uD83D\uDC4D',
            nm: '\uD83D\uDE0A',
            wyd: '\uD83D\uDC40',
            bday: '\uD83C\uDF82',
            birthday: '\uD83C\uDF82',
            gift: '\uD83C\uDF81',
            pray: '\uD83D\uDE4F',
            strong: '\uD83D\uDCAA',
            muscle: '\uD83D\uDCAA',
            phone: '\uD83D\uDCF1',
            laptop: '\uD83D\uDCBB',
            camera: '\uD83D\uDCF7',
            book: '\uD83D\uDCDA',
            bell: '\uD83D\uDD14',
            lock: '\uD83D\uDD12',
            key: '\uD83D\uDD11',
            lolol: '\uD83D\uDE02',
            kek: '\uD83D\uDE02',
            lul: '\uD83D\uDE02',
            roflmao: '\uD83D\uDE02',
            joy: '\uD83D\uDE02',
            sob: '\uD83D\uDE2D',
            bruh: '\uD83D\uDE12',
            yikes: '\uD83D\uDE33',
            sheesh: '\uD83D\uDE33',
            cringe: '\uD83D\uDE35',
            based: '\uD83D\uDC4D',
            fr: '\uD83D\uDCAF',
            ngl: '\uD83D\uDE10',
            tbh: '\uD83D\uDE10',
            smh: '\uD83D\uDE14',
            fml: '\uD83D\uDE29',
            noway: '\uD83D\uDE32',
            pog: '\uD83D\uDE32',
            poggers: '\uD83D\uDE32',
            bussin: '\uD83D\uDE0B',
            mid: '\uD83D\uDE10',
            salty: '\uD83E\uDD28',
            petty: '\uD83D\uDE12',
            shook: '\uD83D\uDE33',
            hyped: '\uD83D\uDE0D',
            excited: '\uD83D\uDE0D',
            nervous: '\uD83D\uDE30',
            scared: '\uD83D\uDE28',
            worried: '\uD83D\uDE1F',
            confused: '\uD83D\uDE15',
            bored: '\uD83D\uDE34',
            annoyed: '\uD83D\uDE12',
            furious: '\uD83D\uDE21',
            grateful: '\uD83D\uDE4F',
            proud: '\uD83D\uDC4F',
            blessed: '\uD83D\uDE4F',
            jealous: '\uD83D\uDE0F',
            lonely: '\uD83D\uDE14',
            awkward: '\uD83D\uDE05',
            embarrassed: '\uD83D\uDE33',
            stressed: '\uD83D\uDE30',
            chill: '\uD83D\uDE0E',
            cozy: '\uD83D\uDE0C',
            inlove: '\uD83D\uDE0D',
            hearteyes: '\uD83D\uDE0D',
            ilu: '\u2764',
            ilysm: '\u2764',
            luv: '\u2764',
            luvu: '\u2764',
            missyou: '\uD83D\uDE22',
            hug: '\uD83E\uDD17',
            hbd: '\uD83C\uDF82',
            ggwp: '\uD83D\uDC4D',
            gl: '\uD83D\uDC4D',
            glhf: '\uD83D\uDC4D',
            hf: '\uD83D\uDC4D',
            ez: '\uD83D\uDE0E',
            noob: '\uD83D\uDE05',
            afk: '\uD83D\uDE34',
            omw: '\uD83D\uDE97',
            nvm: '\uD83D\uDE10',
            jk: '\uD83D\uDE09',
            rn: '\u23F0',
            asap: '\u26A1',
            facepalm: '\uD83E\uDD26',
            eyeroll: '\uD83D\uDE44',
            duh: '\uD83D\uDE44',
            smart: '\uD83E\uDDE0',
            brain: '\uD83E\uDDE0',
            sushi: '\uD83C\uDF63',
            ramen: '\uD83C\uDF5C',
            donut: '\uD83C\uDF69',
            icecream: '\uD83C\uDF68',
            chocolate: '\uD83C\uDF6B',
            candy: '\uD83C\uDF6C',
            popcorn: '\uD83C\uDF7F',
            watermelon: '\uD83C\uDF49',
            strawberry: '\uD83C\uDF53',
            avocado: '\uD83E\uDD51',
            bacon: '\uD83E\uDD53',
            egg: '\uD83E\uDD5A',
            bunny: '\uD83D\uDC30',
            wolf: '\uD83D\uDC3A',
            fox: '\uD83E\uDD8A',
            frog: '\uD83D\uDC38',
            butterfly: '\uD83E\uDD8B',
            bee: '\uD83D\uDC1D',
            whale: '\uD83D\uDC0B',
            diamond: '\uD83D\uDC8E',
            gem: '\uD83D\uDC8E',
            trophy: '\uD83C\uDFC6',
            medal: '\uD83C\uDFC6',
            target: '\uD83C\uDFAF',
            bomb: '\uD83D\uDCA3',
            boom: '\uD83D\uDCA5',
            zap: '\u26A1',
            bulb: '\uD83D\uDCA1',
            idea: '\uD83D\uDCA1',
            check: '\u2705',
            cross: '\u274C',
            home: '\uD83C\uDFE0',
            work: '\uD83D\uDCBC',
            school: '\uD83C\uDFEB',
            dance: '\uD83D\uDC83',
            gym: '\uD83D\uDCAA',
            swim: '\uD83C\uDFCA',
            soccer: '\u26BD',
            basketball: '\uD83C\uDFC0',
            football: '\uD83C\uDFC8',
            vacation: '\uD83C\uDFD6',
            travel: '\u2708',
            sunset: '\uD83C\uDF05',
            storm: '\u26C8',
            lightning: '\u26A1',
            dick: '\uD83C\uDF46',
            cock: '\uD83C\uDF46',
            penis: '\uD83C\uDF46',
            eggplant: '\uD83C\uDF46',
            ass: '\uD83C\uDF51',
            booty: '\uD83C\uDF51',
            butt: '\uD83C\uDF51',
            peach: '\uD83C\uDF51',
            thicc: '\uD83C\uDF51',
            thick: '\uD83C\uDF51',
            cum: '\uD83D\uDCA6',
            wet: '\uD83D\uDCA6',
            drip: '\uD83D\uDCA6',
            squirt: '\uD83D\uDCA6',
            horny: '\uD83D\uDE0F',
            sexy: '\uD83D\uDE0D',
            naughty: '\uD83D\uDE08',
            nsfw: '\uD83D\uDD1E',
            nude: '\uD83D\uDE48',
            spicy: '\uD83C\uDF36',
            tongue: '\uD83D\uDC45',
            lick: '\uD83D\uDC45',
            cherries: '\uD83C\uDF52',
            lips: '\uD83D\uDC8B',
            strip: '\uD83D\uDC83',
            bedroom: '\uD83D\uDECF',
            flex: '\uD83D\uDCAA',
            roast: '\uD83D\uDD25',
            valid: '\u2705',
            periodt: '\uD83D\uDC85',
            simp: '\uD83E\uDD7A',
            stan: '\u2764',
            ship: '\uD83D\uDEA2',
            glow: '\u2728',
            glowup: '\u2728',
            ghosted: '\uD83D\uDC7B',
            blocked: '\uD83D\uDEAB',
            mute: '\uD83D\uDD07',
            dm: '\uD83D\uDCE9',
            pic: '\uD83D\uDCF7',
            selfie: '\uD83E\uDD33',
            rage: '\uD83D\uDE24',
            triggered: '\uD83D\uDE24',
            trash: '\uD83D\uDDD1',
            clown: '\uD83E\uDD21',
            bozo: '\uD83E\uDD21',
            ratio: '\uD83D\uDCC9',
            dub: '\uD83C\uDFC6',
            snipe: '\uD83C\uDFAF',
            stonks: '\uD83D\uDCC8',
            broke: '\uD83D\uDCB8',
            shop: '\uD83D\uDED2',
            nails: '\uD83D\uDC85',
            makeup: '\uD83D\uDC84',
            dress: '\uD83D\uDC57',
            shoes: '\uD83D\uDC60',
            ring: '\uD83D\uDC8D',
            wedding: '\uD83D\uDC92',
            baby: '\uD83D\uDC76',
            pasta: '\uD83C\uDF5D',
            noodles: '\uD83C\uDF5C',
            hotdog: '\uD83C\uDF2D',
            sandwich: '\uD83E\uDD6A',
            milk: '\uD83E\uDD5B',
            champagne: '\uD83C\uDF7E',
            whiskey: '\uD83E\uDD43',
            cocktail: '\uD83C\uDF79',
            smoke: '\uD83D\uDCA8',
            drunk: '\uD83E\uDD74',
            wasted: '\uD83E\uDD74',
            hangover: '\uD83E\uDD15',
            pill: '\uD83D\uDC8A',
            yoga: '\uD83E\uDDD8',
            bike: '\uD83D\uDEB4',
            train: '\uD83D\uDE86',
            bus: '\uD83D\uDE8C',
            taxi: '\uD83D\uDE95',
            rocket: '\uD83D\uDE80',
            ufo: '\uD83D\uDEF8',
            knife: '\uD83D\uDD2A',
            sword: '\u2694',
            wizard: '\uD83E\uDDD9',
            vampire: '\uD83E\uDDDB',
            zombie: '\uD83E\uDDDF',
            pumpkin: '\uD83C\uDF83',
            firework: '\uD83C\uDF86',
            balloon: '\uD83C\uDF88',
            confetti: '\uD83C\uDF8A',
            first: '\uD83E\uDD47',
            second: '\uD83E\uDD48',
            third: '\uD83E\uDD49',
            dice: '\uD83C\uDFB2',
            poker: '\uD83C\uDCCF',
            guitar: '\uD83C\uDFB8',
            mic: '\uD83C\uDFA4',
            headphone: '\uD83C\uDFA7',
            movie: '\uD83C\uDFAC',
            tv: '\uD83D\uDCFA',
            dream: '\uD83D\uDCAD',
            nightmare: '\uD83D\uDE31',
            scream: '\uD83D\uDE31',
            mindblown: '\uD83E\uDD2F',
            sneeze: '\uD83E\uDD27',
            cough: '\uD83D\uDE37',
            bandaid: '\uD83E\uDE79',
            fix: '\uD83D\uDD27',
            handshake: '\uD83E\uDD1D',
            fistbump: '\uD83D\uDC4A',
            peace: '\u270C',
            luck: '\uD83C\uDF40',
            crystal: '\uD83D\uDD2E',
            magic: '\uD83E\uDE84',
            ':3': '\uD83D\uDE0A',
            '^_^': '\uD83D\uDE0A',
            xd: '\uD83D\uDE02',
            ':*': '\uD83D\uDE18',
            'B)': '\uD83D\uDE0E',
            '8)': '\uD83D\uDE0E',
            ':@': '\uD83D\uDE21',
            '>:(': '\uD83D\uDE20',
            T_T: '\uD83D\uDE22',
            '-_-': '\uD83D\uDE11',
            'o.o': '\uD83D\uDE33',
            '^^': '\uD83D\uDE0A',
            '<3': '\u2764',
            '</3': '\uD83D\uDC94',
            ':)': '\uD83D\uDE0A',
            ':-)': '\uD83D\uDE0A',
            '=)': '\uD83D\uDE0A',
            ':d': '\uD83D\uDE04',
            ':-d': '\uD83D\uDE04',
            '=d': '\uD83D\uDE04',
            ';)': '\uD83D\uDE09',
            ';-)': '\uD83D\uDE09',
            ':p': '\uD83D\uDE1B',
            ':-p': '\uD83D\uDE1B',
            ':(': '\uD83D\uDE14',
            ':-(': '\uD83D\uDE14',
            ":'(": '\uD83D\uDE22',
            ':o': '\uD83D\uDE2E',
            ':-o': '\uD83D\uDE2E',
            ':|': '\uD83D\uDE10',
            ':/': '\uD83D\uDE15',
            ':\\': '\uD83D\uDE15',
            '<33': '\uD83D\uDC95'
        };
    }

    function getMode() {
        if (runtimeMode) {
            return runtimeMode;
        }
        try {
            if (window.localStorage && localStorage.getItem(MODE_KEY) === MODE_APPEND) {
                runtimeMode = MODE_APPEND;
                return MODE_APPEND;
            }
        } catch (e) {
        }
        runtimeMode = MODE_REPLACE;
        return MODE_REPLACE;
    }

    function setMode(mode) {
        runtimeMode = mode === MODE_APPEND ? MODE_APPEND : MODE_REPLACE;
        try {
            if (window.localStorage) {
                localStorage.setItem(MODE_KEY, runtimeMode);
            }
        } catch (e) {
        }
    }

    function getEnabled() {
        if (runtimeEnabled !== null) {
            return runtimeEnabled;
        }
        try {
            if (window.localStorage && localStorage.getItem(ENABLED_KEY) === '0') {
                runtimeEnabled = false;
                return false;
            }
        } catch (e) {
        }
        runtimeEnabled = true;
        return true;
    }

    function setEnabled(enabled) {
        runtimeEnabled = !!enabled;
        try {
            if (window.localStorage) {
                localStorage.setItem(ENABLED_KEY, runtimeEnabled ? '1' : '0');
            }
        } catch (e) {
        }
    }

    function isShortcutChar(ch) {
        var code = ch.charCodeAt(0);
        if (code >= 48 && code <= 57) {
            return true;
        }
        if (code >= 65 && code <= 90) {
            return true;
        }
        if (code >= 97 && code <= 122) {
            return true;
        }
        return ch === ':' || ch === ';' || ch === '<' || ch === '>' || ch === "'" || ch === '-' || ch === '=' || ch === '\\' || ch === '|' || ch === '/';
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

    function inputText(input) {
        var hint = input.getAttribute('hint') || '';
        var val = input.value || '';
        if (input.className.indexOf('hint') !== -1 && val === hint) {
            return '';
        }
        return val;
    }

    function lookupShortcut(word) {
        var shortcuts = window.IMVU_EMOJI_SHORTCUTS;
        if (!word || !shortcuts) {
            return null;
        }
        if (shortcuts[word]) {
            return shortcuts[word];
        }
        if (shortcuts[word.toLowerCase()]) {
            return shortcuts[word.toLowerCase()];
        }
        return null;
    }

    function tokenBeforeCursor(input) {
        var val = inputText(input);
        var end = typeof input.selectionStart === 'number' ? input.selectionStart : val.length;
        var start = end;
        while (start > 0 && isShortcutChar(val.charAt(start - 1))) {
            start -= 1;
        }
        return {
            word: val.substring(start, end),
            start: start,
            end: end
        };
    }

    function attach(textChatRoot) {
        if (!textChatRoot || textChatRoot.getAttribute(MARKER) === '1') {
            return;
        }

        var input = textChatRoot.querySelector('input');
        var host = textChatRoot.querySelector('#input-row-wrapper')
            || textChatRoot.querySelector('#inputRow')
            || textChatRoot;
        if (!input || !host) {
            return;
        }

        var uiHost = document.createElement('div');
        uiHost.className = 'imvu-emoji-suggest-host';

        var bar = document.createElement('div');
        bar.className = 'imvu-emoji-suggest hidden';

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'imvu-emoji-suggest-btn';
        btn.innerHTML = '<span class="imvu-emoji-suggest-word"></span>'
            + '<span class="imvu-emoji-suggest-arrow">&rarr;</span>'
            + '<img class="imvu-emoji-suggest-img" alt="" draggable="false">';
        bar.appendChild(btn);
        uiHost.appendChild(bar);
        host.appendChild(uiHost);

        var wordEl = btn.getElementsByTagName('span')[0];
        var arrowEl = btn.getElementsByTagName('span')[1];
        var imgEl = btn.getElementsByTagName('img')[0];
        var active = null;
        var hideTimer = null;

        function updateModeUi() {
            var mode = getMode();
            arrowEl.innerHTML = mode === MODE_APPEND ? '+' : '&rarr;';
            btn.title = mode === MODE_APPEND
                ? 'Add emoji after word (Tab)'
                : 'Replace word with emoji (Tab)';
        }

        function hideBar() {
            bar.className = 'imvu-emoji-suggest hidden';
            active = null;
        }

        function showBar(match) {
            var hex;
            if (!match || !match.emoji) {
                hideBar();
                return;
            }
            hex = cache.hexFromEmoji(match.emoji);
            if (!hex) {
                hideBar();
                return;
            }
            active = match;
            wordEl.innerHTML = '';
            wordEl.appendChild(document.createTextNode(match.word));
            imgEl.src = cache.getSrc(hex);
            cache.upgradeImg(imgEl, hex);
            cache.persistHex(hex);
            updateModeUi();
            bar.className = 'imvu-emoji-suggest';
        }

        function applySuggestion() {
            var val;
            var nextPos;
            var mode;
            var replacement;
            if (!active) {
                return false;
            }
            clearHint(input);
            val = inputText(input);
            if (!val && input.value) {
                val = input.value;
            }
            mode = getMode();
            if (mode === MODE_APPEND) {
                replacement = active.word + ' ' + active.emoji;
                input.value = val.substring(0, active.start) + replacement + val.substring(active.end);
                nextPos = active.start + replacement.length;
            } else {
                input.value = val.substring(0, active.start) + active.emoji + val.substring(active.end);
                nextPos = active.start + active.emoji.length;
            }
            if (typeof input.selectionStart === 'number') {
                input.selectionStart = nextPos;
                input.selectionEnd = nextPos;
            }
            hideBar();
            input.focus();
            return true;
        }

        function refresh() {
            var token;
            var emoji;
            if (!getEnabled()) {
                hideBar();
                return;
            }
            token = tokenBeforeCursor(input);
            if (!token.word || token.word.length < 2) {
                hideBar();
                return;
            }
            emoji = lookupShortcut(token.word);
            if (!emoji) {
                hideBar();
                return;
            }
            showBar({
                word: token.word,
                emoji: emoji,
                start: token.start,
                end: token.end
            });
        }

        function isTabKey(evt) {
            if (!evt) {
                return false;
            }
            var key = evt.keyCode || evt.which;
            return key === 9;
        }

        function cancelTab(evt) {
            if (evt.preventDefault) {
                evt.preventDefault();
            }
            evt.returnValue = false;
            if (evt.stopPropagation) {
                evt.stopPropagation();
            }
        }

        function tryAcceptTab(evt) {
            if (!isTabKey(evt) || !getEnabled()) {
                return false;
            }
            if (!active) {
                refresh();
            }
            if (!active) {
                return false;
            }
            cancelTab(evt);
            applySuggestion();
            return true;
        }

        function onInputKeyup(evt) {
            evt = evt || window.event;
            if (evt && (isTabKey(evt) || evt.keyCode === 27)) {
                return;
            }
            refresh();
        }

        function onInputKeydown(evt) {
            evt = evt || window.event;
            if (tryAcceptTab(evt)) {
                return false;
            }
            if (evt && evt.keyCode === 27) {
                hideBar();
            }
        }

        function onInputKeypress(evt) {
            evt = evt || window.event;
            if (tryAcceptTab(evt)) {
                return false;
            }
        }

        function onInputBlur() {
            if (hideTimer) {
                clearTimeout(hideTimer);
            }
            hideTimer = setTimeout(hideBar, 150);
        }

        function onInputFocus() {
            if (hideTimer) {
                clearTimeout(hideTimer);
                hideTimer = null;
            }
            refresh();
        }

        if (input.addEventListener) {
            input.addEventListener('keyup', onInputKeyup, false);
            input.addEventListener('keydown', onInputKeydown, true);
            input.addEventListener('keypress', onInputKeypress, true);
            input.addEventListener('blur', onInputBlur, false);
            input.addEventListener('focus', onInputFocus, false);
        } else {
            input.onkeyup = onInputKeyup;
            input.onkeydown = onInputKeydown;
            input.onkeypress = onInputKeypress;
            input.onblur = onInputBlur;
            input.onfocus = onInputFocus;
        }

        btn.onmousedown = function (evt) {
            if (evt.preventDefault) {
                evt.preventDefault();
            }
            applySuggestion();
            return false;
        };

        function refreshSettingsUi() {
            updateModeUi();
            if (!getEnabled()) {
                hideBar();
            }
        }

        refreshSettingsUi();
        IMVU.Client.ChatEmojiSuggestions.refreshUi = refreshSettingsUi;
        textChatRoot.setAttribute(MARKER, '1');
    }

    IMVU.Client.ChatEmojiSuggestions = {
        attach: attach,
        getMode: getMode,
        setMode: setMode,
        getEnabled: getEnabled,
        setEnabled: setEnabled,
        refreshUi: null
    };

    function tryInit() {
        var root = document.getElementById('text-chat');
        if (root && root.querySelector('input')) {
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
