import os
import subprocess
from unittest.mock import patch

from imvu_toolkit.imvu_process import (
    ensure_imvu_closed,
    imvu_exe_path,
    start_imvu,
    wait_for_imvu_closed,
)


def test_imvu_exe_path():
    assert imvu_exe_path(r"C:\Users\You\AppData\Roaming\IMVUClient").endswith(
        os.path.join("IMVUClient", "IMVUClient.exe")
    )


@patch("imvu_toolkit.imvu_process.subprocess.Popen")
def test_start_imvu_launches_exe(mock_popen, tmp_path):
    imvu_dir = tmp_path / "IMVUClient"
    imvu_dir.mkdir()
    exe = imvu_dir / "IMVUClient.exe"
    exe.write_bytes(b"")

    ok, err = start_imvu(str(imvu_dir))

    assert ok is True
    assert err is None
    mock_popen.assert_called_once_with([str(exe)], cwd=str(imvu_dir))


def test_start_imvu_missing_exe(tmp_path):
    ok, err = start_imvu(str(tmp_path))

    assert ok is False
    assert "IMVUClient.exe not found" in err


@patch("imvu_toolkit.imvu_process.imvu_is_running", return_value=False)
def test_wait_for_imvu_closed_when_not_running(_mock_running, tmp_path):
    ok, err = wait_for_imvu_closed(str(tmp_path))

    assert ok is True
    assert err is None


@patch("imvu_toolkit.imvu_process.time.sleep")
@patch("imvu_toolkit.imvu_process.imvu_is_running", side_effect=[True, True, False])
def test_wait_for_imvu_closed_polls_until_exit(_mock_running, _mock_sleep, tmp_path):
    ok, err = wait_for_imvu_closed(str(tmp_path), poll_interval=0.01, timeout=5)

    assert ok is True
    assert err is None


@patch("imvu_toolkit.imvu_process.time.sleep")
@patch("imvu_toolkit.imvu_process.imvu_is_running", side_effect=[True, True, False])
@patch("imvu_toolkit.imvu_process.sys.stdout")
def test_wait_for_imvu_closed_gui_status_lines(_mock_stdout, _mock_running, _mock_sleep, tmp_path):
    _mock_stdout.isatty.return_value = False

    ok, err = wait_for_imvu_closed(str(tmp_path), poll_interval=0.01, timeout=5)

    assert ok is True
    assert err is None
    printed = " ".join(str(c) for c in _mock_stdout.write.call_args_list)
    assert "\r" not in printed


def test_hidden_subprocess_kwargs_on_windows():
    from imvu_toolkit.imvu_process import _hidden_subprocess_kwargs

    kwargs = _hidden_subprocess_kwargs()
    if os.name == "nt":
        assert kwargs.get("creationflags") == subprocess.CREATE_NO_WINDOW
    else:
        assert kwargs == {}


@patch("imvu_toolkit.imvu_process.imvu_is_running", return_value=True)
def test_ensure_imvu_closed_no_close_imvu_fails_fast(_mock_running, tmp_path):
    ok, err = ensure_imvu_closed(str(tmp_path), force=False, no_close_imvu=True)

    assert ok is False
    assert "Close IMVU manually" in err


@patch("imvu_toolkit.imvu_process.wait_for_imvu_closed", return_value=(True, None))
@patch("imvu_toolkit.imvu_process.imvu_is_running", return_value=True)
def test_ensure_imvu_closed_waits_by_default(_mock_running, mock_wait, tmp_path):
    ok, err = ensure_imvu_closed(str(tmp_path), force=False, no_close_imvu=False)

    assert ok is True
    mock_wait.assert_called_once()
