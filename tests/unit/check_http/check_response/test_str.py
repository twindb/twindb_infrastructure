from twindb_infrastructure.check_http import CheckResponse


def test_str():
    resp = CheckResponse(
        message='foo'
    )
    assert str(resp) == 'foo'
