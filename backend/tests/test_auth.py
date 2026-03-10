from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hash_is_not_plain_text():
    hashed = hash_password("mysecretpassword")
    assert hashed != "mysecretpassword"


def test_correct_password_verifies():
    hashed = hash_password("mysecretpassword")
    assert verify_password("mysecretpassword", hashed) is True


def test_wrong_password_fails():
    hashed = hash_password("mysecretpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_token_round_trip():
    token = create_access_token("user-123")
    decoded_id = decode_access_token(token)
    assert decoded_id == "user-123"


def test_tampered_token_returns_none():
    token = create_access_token("user-123")
    bad_token = token + "tampered"
    assert decode_access_token(bad_token) is None
