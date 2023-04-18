from apinator.common import PathStr


def test_pathstr_common_operations():
    """Test basic operations on path strings."""
    a = PathStr.parse_obj("a")
    b = PathStr.parse_obj("b")
    b_slash = PathStr.parse_obj("/b/")

    assert str(a) == "/a"
    assert str(b) == "/b"
    assert str(a / b) == "/a/b"
    assert str(a / b_slash) == "/a/b"
    assert str(a / "c") == "/a/c"
    assert str(a / "/c/") == "/a/c"
    assert str("c" / a) == "/c/a"
    assert str(a / 5) == "/a/5"
