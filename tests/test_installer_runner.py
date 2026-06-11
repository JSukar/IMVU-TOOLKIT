from imvu_toolkit.installer.profiles import get_profile
from imvu_toolkit.installer.runner import run_patch


def test_run_patch_import():
    assert callable(run_patch)


def test_installer_profiles():
    emoji = get_profile("emoji")
    antibot = get_profile("antibot")
    assert emoji.id == "emoji"
    assert antibot.id == "antibot"
    assert "shield" in antibot.install_success.lower()
