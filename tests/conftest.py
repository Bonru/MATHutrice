"""Lets the tests import the project with no .env, as in CI."""

import os

import dotenv

# The project calls load_dotenv() at import time. A developer's .env must not
# leak into the tests, and CI has none: make it a no-op before any import.
dotenv.load_dotenv = lambda *args, **kwargs: False

# Importing the LLM client and the database needs these settings. Dummy values:
# no test reaches a real LLM or a real database.
os.environ.setdefault("LLM_BASE_URL", "http://llm.invalid/v1")
os.environ.setdefault("LLM_API_KEY", "dummy-key-for-tests")
os.environ.setdefault("LLM_MODEL", "dummy-model")
os.environ.setdefault("DATABASE_URL", "sqlite://")
