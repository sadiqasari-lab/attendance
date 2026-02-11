"""Staging settings — mirrors production with relaxed throttling."""
from .production import *  # noqa: F401, F403

# Slightly relaxed for QA testing
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "100/minute",
    "user": "1000/minute",
}
