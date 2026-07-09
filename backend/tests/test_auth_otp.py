from backend.routes.auth import _clear_otp_state, _get_otp_state, _store_otp_state


def test_otp_state_round_trip():
    token = _store_otp_state({"kind": "voter", "voter_id": "V1"}, "123456")

    state = _get_otp_state(token)
    assert state is not None
    assert state["otp"] == "123456"
    assert state["context"]["voter_id"] == "V1"

    _clear_otp_state(token)
    assert _get_otp_state(token) is None
