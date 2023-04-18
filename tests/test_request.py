from apinator.common import Request


def test_request_common_operations():
    req1 = Request()
    req2 = req1.with_options(query={"a": 1})
    req3 = req2.with_options(query={"b": 2})

    assert req1.query == {}
    assert req2.query == {"a": 1}
    assert req3.query == {"a": 1, "b": 2}
