"""
observability.py — Production signals: errors and logs, sent to PostHog.

Three settings, all or none:
  - POSTHOG_PROJECT_TOKEN : the project's token (phc_...), a secret
  - POSTHOG_HOST          : https://eu.i.posthog.com
  - POSTHOG_ENVIRONMENT   : staging or production, the tag of every event

With none set, nothing is sent and the service runs as before. With only some
set, the service refuses to start, naming the first one missing.
"""

import logging
import os

SETTINGS = ("POSTHOG_PROJECT_TOKEN", "POSTHOG_HOST", "POSTHOG_ENVIRONMENT")

# The process's PostHog client, set by start_client; None when signals are off.
client = None


def read_settings() -> dict | None:
    """The three settings, or None when none is set."""
    values = {name: os.getenv(name, "") for name in SETTINGS}
    if not any(values.values()):
        return None
    for name in SETTINGS:
        if not values[name]:
            raise ValueError(f"{name} missing")
    return values


def start_client(settings: dict):
    """The PostHog client for this process: errors, tagged with the environment."""
    global client
    from posthog import Posthog

    client = Posthog(
        settings["POSTHOG_PROJECT_TOKEN"],
        host=settings["POSTHOG_HOST"],
        enable_exception_autocapture=True,
        super_properties={"environment": settings["POSTHOG_ENVIRONMENT"]},
    )
    return client


def report(exception: BaseException) -> None:
    """Reports an exception the code caught and answered for itself.

    Called before the code answers, inside the request's PostHog context, so
    the error names the signed-in user. With signals off, does nothing; it
    never changes the answer.
    """
    if client is not None:
        client.capture_exception(exception)


def start_logs(settings: dict):
    """Sends every INFO log line to PostHog Logs; returns the provider to shut down."""
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import Resource

    provider = LoggerProvider(
        resource=Resource.create(
            {
                "service.name": "mathutrice",
                "deployment.environment": settings["POSTHOG_ENVIRONMENT"],
            }
        )
    )
    provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(
                endpoint=settings["POSTHOG_HOST"].rstrip("/") + "/i/v1/logs",
                headers={"Authorization": f"Bearer {settings['POSTHOG_PROJECT_TOKEN']}"},
            )
        )
    )
    handler = LoggingHandler(level=logging.INFO, logger_provider=provider)

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    # A logger that does not propagate never reaches the root: give it the
    # handler too. One that propagates already does, and would log twice.
    for logger in logging.Logger.manager.loggerDict.values():
        if isinstance(logger, logging.Logger) and not logger.propagate:
            logger.addHandler(handler)
    return provider
