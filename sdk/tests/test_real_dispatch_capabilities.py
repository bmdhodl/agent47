"""Regressions for selecting real provider compatibility tests."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from test_real_dispatch import responses_sdk


@pytest.mark.parametrize("has_responses", [True, False])
def test_responses_probe_uses_the_instance_and_closes_it(has_responses):
    clients = []

    class Client:
        def __init__(self, *, api_key, http_client):
            assert api_key == "sk-compat"
            assert http_client is not None
            self.closed = False
            if has_responses:
                self.responses = object()
            clients.append(self)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.closed = True

    sdk = SimpleNamespace(OpenAI=Client, DefaultHttpxClient=object)
    probe = responses_sdk.__wrapped__(sdk)
    if has_responses:
        try:
            assert next(probe) is sdk
        except pytest.skip.Exception:
            pytest.fail("The Responses API exists on the instance but the fixture skipped it.")
        with pytest.raises(StopIteration):
            next(probe)
    else:
        with pytest.raises(pytest.skip.Exception):
            next(probe)
    assert len(clients) == 1
    assert clients[0].closed
