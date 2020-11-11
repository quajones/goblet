import logging
import os 
import sys
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler, setup_logging
from google.cloud.logging.resource import Resource
import uuid
from jsonschema import validate, ValidationError
from google.cloud import pubsub_v1
import base64
import json

from goblet.decorators import LegacyDecoratorAPI, Register_Handlers

logging.basicConfig()

class Goblet(LegacyDecoratorAPI, Register_Handlers):
    def __init__(self, function_name="goblet", region="us-east4", stackdriver=False, env=None):
        super(Goblet, self).__init__(function_name=function_name)
        self.function_name = function_name
        self.region = region
        self.log = logging.getLogger(__name__)
        self.data = None
        self.event = None
        self.context = None
        self.correlation_id = None
        self.headers = {}
        if stackdriver:
            self._initialize_stackdriver_logging()
            self.log = logging.getLogger(name=__name__)

    def _initialize_stackdriver_logging(self):
        stackdriver_client = google.cloud.logging.Client()
        stackdriver_handler = CloudLoggingHandler(stackdriver_client,name=__name__, resource=self.log_resource, labels={})
        setup_logging(stackdriver_handler)

    @property
    def log_resource(self):
        return Resource(type="cloud_function", 
                labels={
                    "function_name": self.function_name, 
                    "region": self.region,
                    "correlation_id": self.correlation_id or "missing"
                },
    )

    def jsonify(self, *args, **kwargs):
        indent = None
        separators = (',', ':')
        headers = {'Content-Type': 'application/json'}
        headers.update(self.headers)

        if args and kwargs:
            raise TypeError('jsonify() behavior undefined when passed both args and kwargs')
        elif len(args) == 1:  # single args are passed directly to dumps()
            data = args[0]
        else:
            data = args or kwargs

        json_string = json.dumps(data, indent=indent, separators=separators)
        return (json_string,200,headers)
