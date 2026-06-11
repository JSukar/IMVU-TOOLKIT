"""Installer UI copy and patch routing for emoji vs antibot builds."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstallerProfile:
    id: str
    window_title: str
    hero_title: str
    subtitle: str
    install_button: str
    restore_confirm: str
    install_success: str
    restore_success: str
    hint: str


PROFILES: dict[str, InstallerProfile] = {
    "emoji": InstallerProfile(
        id="emoji",
        window_title="IMVU Emoji Patch Installer",
        hero_title="Emoji Patch Installer",
        subtitle="Twemoji chat rendering + emoji picker",
        install_button="Install Emoji Patch",
        restore_confirm=(
            "This removes the emoji patch and restores "
            "library.zip / imvuContent.jar backups.\n\nContinue?"
        ),
        install_success="Install complete. Click the smiley button beside Send in chat.",
        restore_success="Restore complete.",
        hint=(
            "If IMVU is open, close it when prompted. "
            "The installer waits, patches, then relaunches IMVU."
        ),
    ),
    "antibot": InstallerProfile(
        id="antibot",
        window_title="IMVU Antibot Patch Installer",
        hero_title="Antibot Patch Installer",
        subtitle="Auto-boot promo bots in rooms you own or mod",
        install_button="Install Antibot Patch",
        restore_confirm=(
            "This removes the antibot patch and restores "
            "library.zip / imvuContent.jar backups.\n\nContinue?"
        ),
        install_success=(
            "Install complete. Use the shield icon beside Send in chat "
            "for protection status and boot log."
        ),
        restore_success="Restore complete.",
        hint=(
            "If IMVU is open, close it when prompted. "
            "The installer waits, patches, then relaunches IMVU."
        ),
    ),
}


def get_profile(profile_id: str) -> InstallerProfile:
    try:
        return PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError("Unknown installer profile: %s" % profile_id) from exc
