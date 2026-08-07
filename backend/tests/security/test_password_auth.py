from app.security.auth import verify_password

DEMO_HASH = "$2b$12$ug0GbmCtlhFDk9JEGOWD0ujC3BogvQhOsPcxyTnXRLSN/U8kxypoG"


def test_correct_demo_password_verifies() -> None:
    assert verify_password("demo123", DEMO_HASH)


def test_wrong_demo_password_fails() -> None:
    assert not verify_password("wrong-password", DEMO_HASH)
