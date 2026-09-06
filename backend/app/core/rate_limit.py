from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
"""Per-IP, in-memory rate limiting (slowapi/limits' default MemoryStorage) --
correct for this app's current single-process deployment, but resets on restart
and isn't shared across multiple instances. If this ever runs behind a load
balancer with more than one backend process, this needs a shared store (e.g.
Redis) instead, or each process enforces its own independent limit.

Tests disable this globally (see tests/conftest.py) since TestClient requests all
share one address and this suite calls /auth/register and /auth/login far more
than any real limit allows; the one test that exercises the limiter itself
re-enables it locally.
"""
