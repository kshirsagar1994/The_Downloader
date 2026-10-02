from app.security.sanitization import sanitize_extension, sanitize_filename


def test_sanitize_filename_removes_traversals():
    assert sanitize_filename("../../../etc/passwd") == "etc_passwd"
    assert sanitize_filename("..\\..\\windows\\system32") == "windows_system32"


def test_sanitize_filename_removes_forbidden_chars():
    dirty = 'My: Cool "Video" <Best> | 2026? *#/'
    clean = sanitize_filename(dirty)
    assert ":" not in clean
    assert '"' not in clean
    assert "<" not in clean
    assert ">" not in clean
    assert "|" not in clean
    assert "?" not in clean
    assert "*" not in clean
    assert "/" not in clean


def test_sanitize_filename_windows_reserved():
    assert sanitize_filename("CON.mp4") == "file_CON.mp4"
    assert sanitize_filename("nul.txt") == "file_nul.txt"
    assert sanitize_filename("aux.mp3") == "file_aux.mp3"


def test_sanitize_extension():
    assert sanitize_extension(".MP4") == "mp4"
    assert sanitize_extension("m4a") == "m4a"
    assert sanitize_extension("..exe$$") == "exe"
