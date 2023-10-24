"""
This library builds on the OpenTelemetry WSGI middleware to track web requests
in Goblet applications.

Usage
-----

.. code-block:: python

    from flask import Flask
    from goblet.resource.plugins.instrumentation.opentelemetry_goblet_instrumentation import GobletInstrumentor

    app = Goblet()

    GobletInstrumentor().instrument_app(app)

    @app.route("/")
    def hello():
        return "Hello!"
"""

from curses.ascii import SP
from typing import Collection
from goblet import Goblet


from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.cloud_trace_propagator import CloudTraceFormatPropagator
from opentelemetry.trace.span import SpanContext, Span
from opentelemetry.trace import Link

import logging


tracer_provider = TracerProvider()
cloud_trace_exporter = CloudTraceSpanExporter()
tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))
trace.set_tracer_provider(tracer_provider)
prop = CloudTraceFormatPropagator()
carrier = {}


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

set_global_textmap(CloudTraceFormatPropagator())


class GobletInstrumentor(BaseInstrumentor):
    # pylint: disable=protected-access,attribute-defined-outside-init
    """An instrumentor for Goblet"""

    def instrumentation_dependencies(self) -> Collection[str]:
        return ("goblet-gcp <= 1.0",)

    @staticmethod
    def _before_request(request):
        """
        X-Cloud-Trace-Context: TRACE_ID/SPAN_ID;o=TRACE_TRUE
        """

        log.info(request.headers)
        log.info(request.headers["Traceparent"])
        # trace_context_header = request.headers["X-Cloud-Trace-Context"]

        # if trace_context_header:
        # log.info(trace_context_header)
        # log.info(type(trace_context_header))

        # info = trace_context_header.split(";")[0].split("/")

        # trace_id = info[0]
        # span_id = info[1]

        trace.get_current_span().__enter__()
        # log.info(f"{trace_id}/{span_id}")
        # print(f"{trace_id}/{span_id}")
        # # incoming_request_context = request.headers.get("x-cloud-trace-context")
        # trace.get_tracer(__name__).start_as_current_span(
        #     request.path,
        #     links=[
        #         Link(
        #             SpanContext(
        #                 trace_id=int(trace_id, 16),
        #                 span_id=int(span_id),
        #                 is_remote=True,
        #             )
        #         )
        #     ],
        # ).__enter__()

        # else:
        #     trace.get_tracer(__name__).start_as_current_span(request.path).__enter__()
        prop.inject(carrier=carrier)
        return request

    @staticmethod
    def _after_request(response):
        trace.get_current_span().end()
        return response

    def _instrument(self, app: Goblet):
        """Instrument the library"""
        app.g.tracer = trace.get_tracer(__name__)
        app.g.prop = prop
        app.g.carrier = carrier
        app.before_request()(self._before_request)
        app.after_request()(self._after_request)

    def instrument_app(self, app: Goblet):
        self.instrument(app=app)

    def _uninstrument(self, **kwargs):
        """Uninstrument the library"""
