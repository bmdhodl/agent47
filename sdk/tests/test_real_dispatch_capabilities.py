"""Regressions for selecting real provider compatibility tests."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from test_real_dispatch import _has_responses


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
    if _has_responses(sdk) is not has_responses:
        pytest.fail("The instance probe misreported the Responses resource.")
    assert len(clients) == 1
    assert clients[0].closed
