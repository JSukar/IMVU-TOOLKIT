# Security Policy

## Scope

This project patches **local IMVU Classic client files** under `%APPDATA%\IMVUClient\`. It does not run a server or collect user data.

## Network use

- The emoji patch loads Twemoji PNGs from **jsDelivr** when chat renders emoji (browser engine inside IMVU).
- `scripts/generate_emoji_list.py` may fetch Unicode `emoji-test.txt` when regenerating the catalog (developer tool only).

## Reporting a vulnerability

If you find a security issue in this toolkit (e.g. unsafe file handling, path traversal in patch scripts):

1. **Do not** open a public issue for exploitable details.
2. Open a [GitHub Security Advisory](https://github.com/JSukar/IMVU-TOOLKIT/security/advisories/new) or contact the maintainer via GitHub.

## Safe use

- Download installers only from [official Releases](https://github.com/JSukar/IMVU-TOOLKIT/releases).
- Review patch scripts before running; all source is in this repository.
- Use `--restore` to revert patches from automatic backups.

## Unsigned binaries

Release `.exe` files are not code-signed. Windows may show “Unknown publisher” — see README for details.
