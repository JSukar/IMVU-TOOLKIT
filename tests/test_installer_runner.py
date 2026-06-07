from imvu_toolkit.installer.runner import run_patch


def test_run_patch_import():
    assert callable(run_patch)
