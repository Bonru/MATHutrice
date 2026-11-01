"""An evaluation test of 20 questions on a slow LLM ends within its deadline.

The number comes from Design Document v1, EPF-MDE/MATHutrice#66: a student in
the session slot waits at most 5 minutes (Assumption D) for an evaluation test.
"""

import json
from dataclasses import dataclass

import httpx
import openai
import pytest

from mathutrice.fonctions_python.main import generate_mixed_test
from mathutrice.llm_deadline import (
    EVALUATION_DEADLINE_S,
    DeadlineClient,
    DeadlineExceeded,
)

QUESTIONS = 20


class FakeClock:
    """Seconds since the start of the test. Only the fake LLM moves it."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


@dataclass
class Call:
    started_at: float
    timeout: float | None
    max_retries: int | None


class SlowFakeLLM:
    """The part of openai.OpenAI the project uses, taking `seconds_per_call`.

    A call whose timeout is shorter than its duration times out, as the real
    client would: the clock moves by the timeout, then APITimeoutError.
    """

    def __init__(self, clock, seconds_per_call):
        self.clock = clock
        self.seconds_per_call = seconds_per_call
        self.calls: list[Call] = []
        self._timeout = None
        self._max_retries = None

    def with_options(self, *, timeout=None, max_retries=None):
        bound = SlowFakeLLM(self.clock, self.seconds_per_call)
        bound.calls = self.calls
        bound._timeout = timeout
        bound._max_retries = max_retries
        return bound

    @property
    def chat(self):
        return self

    @property
    def completions(self):
        return self

    def create(self, **kwargs):
        self.calls.append(Call(self.clock.now, self._timeout, self._max_retries))
        if self._timeout is not None and self._timeout < self.seconds_per_call:
            self.clock.now += self._timeout
            raise openai.APITimeoutError(
                request=httpx.Request("POST", "http://llm.invalid/v1/chat/completions")
            )
        self.clock.now += self.seconds_per_call
        content = json.dumps({"question": "Calculer 1 + 1.", "correct_answer": "2"})
        message = type("Message", (), {"content": content})
        choice = type("Choice", (), {"message": message})
        return type("Completion", (), {"choices": [choice]})


def evaluation(llm):
    """Twenty open-answer questions, as one evaluation test asks for them."""
    return generate_mixed_test(
        notion="trigonometrie", niveau="basique", n_qro=QUESTIONS, llm=llm
    )


def test_the_deadline_is_the_number_in_the_design_document():
    assert EVALUATION_DEADLINE_S == 5 * 60


def test_twenty_questions_on_a_slow_llm_stop_at_the_deadline():
    clock = FakeClock()
    slow = SlowFakeLLM(clock, seconds_per_call=40.0)

    with pytest.raises(DeadlineExceeded):
        evaluation(DeadlineClient(slow, clock=clock))

    # The student waited no longer than the number.
    assert clock.now <= EVALUATION_DEADLINE_S
    # No call started once the deadline had passed.
    assert all(call.started_at < EVALUATION_DEADLINE_S for call in slow.calls)
    # Each call was given only the time left, and no hidden retries.
    for call in slow.calls:
        assert call.timeout <= EVALUATION_DEADLINE_S - call.started_at
        assert call.max_retries == 0
    # It gave up before asking for all twenty.
    assert len(slow.calls) < QUESTIONS


def test_twenty_questions_on_a_typical_llm_all_arrive():
    clock = FakeClock()
    typical = SlowFakeLLM(clock, seconds_per_call=2.3)  # measured, #66 Assumption B

    questions = evaluation(DeadlineClient(typical, clock=clock))

    assert len(questions) == len(typical.calls) > 0
    assert clock.now <= EVALUATION_DEADLINE_S
