"""DeadlineClient: the LLM client, with one deadline for many calls.

What it hides from its callers:
  - the clock, and the time left before the deadline;
  - the timeout and the retries each call gets: only the time left, and no
    retry the deadline has not budgeted for;
  - how a call that runs out of time fails (openai.APITimeoutError).

What it promises:
  - it looks like the part of openai.OpenAI the project uses,
    `.chat.completions.create(...)`, so a caller passes it where it would pass
    the client;
  - once the deadline has passed, it starts no other call and raises
    DeadlineExceeded, so the caller can tell the student;
  - every other error of the client reaches the caller unchanged.
"""

import time

import openai

# Design Document v1, EPF-MDE/MATHutrice#66, Assumption D: a student in the
# 30-minute session slot waits at most 5 minutes for an evaluation test.
EVALUATION_DEADLINE_S = 5 * 60


class DeadlineExceeded(Exception):
    """The deadline passed before the work was done."""

    def __init__(self, budget_s: float):
        super().__init__(f"the {budget_s:.0f} s deadline passed")
        self.budget_s = budget_s


class DeadlineClient:
    """Wraps an openai.OpenAI client; every call shares one deadline.

    client:   the OpenAI client, passed by the caller (never the global one).
    budget_s: seconds from now until the deadline.
    clock:    seconds, monotonic; tests pass a fake one.
    """

    def __init__(self, client, budget_s: float = EVALUATION_DEADLINE_S, clock=time.monotonic):
        self._client = client
        self._budget_s = budget_s
        self._clock = clock
        self._deadline = clock() + budget_s

    @property
    def chat(self):
        return self

    @property
    def completions(self):
        return self

    def create(self, **kwargs):
        time_left = self._deadline - self._clock()
        if time_left <= 0:
            raise DeadlineExceeded(self._budget_s)
        bounded = self._client.with_options(timeout=time_left, max_retries=0)
        try:
            return bounded.chat.completions.create(**kwargs)
        except openai.APITimeoutError as error:
            raise DeadlineExceeded(self._budget_s) from error
