"""Security regressions for the MCP runtime's JWT dependency."""

import base64

import jwt
import pytest


@pytest.mark.parametrize("use_key_lookup", [False, True])
def test_recursive_unsigned_payload_raises_documented_error(use_key_lookup, monkeypatch):
    """REGRESSION: GHSA-42vr-xj54-vc7v escaped as an uncaught RecursionError."""
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=")
    payload = base64.urlsafe_b64encode(b"[" * 20_000 + b"]" * 20_000).rstrip(b"=")
    token = (header + b"." + payload + b".Zm9yZ2Vk").decode("ascii")

    def reject_network(*args, **kwargs):
        pytest.fail("Malformed payload must fail before any JWKS network request")

    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", reject_network)
    with pytest.raises(jwt.DecodeError):
        if use_key_lookup:
            jwt.PyJWKClient("https://example.invalid/jwks").get_signing_key_from_jwt(token)
        else:
            jwt.decode(token, options={"verify_signature": False})
