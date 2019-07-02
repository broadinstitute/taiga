import yaml
import jsonschema
import jsonpointer
from functools import wraps
import os
import json
import logging

log = logging.getLogger(__name__)

CACHED_SWAGGER_SPEC = None


def expand_refs(obj, root):
    if isinstance(obj, list):
        return [expand_refs(x, root) for x in obj]
    elif isinstance(obj, dict):
        if len(obj) == 1 and "$ref" in obj:
            ptr_str = obj["$ref"]
            assert ptr_str.startswith("#")
            ref = jsonpointer.JsonPointer(ptr_str[1:])
            return expand_refs(ref.get(root), root)
        else:
            return dict([(k, expand_refs(v, root)) for k, v in obj.items()])
    return obj


def load_endpoint_per_operation(filename):
    with open(filename) as fd:
        spec = yaml.load(fd, Loader=yaml.SafeLoader)
    spec = expand_refs(spec, spec)

    endpoint_per_operation = {}

    for path, path_obj in spec["paths"].items():
        for method, endpoint in path_obj.items():
            endpoint_per_operation[endpoint["operationId"]] = endpoint

    return endpoint_per_operation


def get_body_parameter(endpoint):
    body_params = [x for x in endpoint.get("parameters", []) if x["in"] == "body"]

    if len(body_params) == 0:
        return None

    assert len(body_params) == 1
    return body_params[0]["name"], body_params[0]["schema"]


def get_response_schema(endpoint):
    return endpoint["responses"][200].get("schema")


def get_endpoint_for(operation_id):
    global CACHED_SWAGGER_SPEC
    if CACHED_SWAGGER_SPEC is None:
        filename = os.path.join(os.path.dirname(__file__), "../swagger/swagger.yaml")
        CACHED_SWAGGER_SPEC = load_endpoint_per_operation(filename)
    return CACHED_SWAGGER_SPEC[operation_id]


import inspect


def validate(endpoint_func):
    @wraps(endpoint_func)
    def execute_with_validation(*args, **kwargs):
        if len(args) > 0:
            positional_arg_names = list(
                inspect.signature(endpoint_func).parameters.keys()
            )
            for name, arg in zip(positional_arg_names, args):
                kwargs[name] = arg

        endpoint = get_endpoint_for(endpoint_func.__name__)
        p = get_body_parameter(endpoint)
        if p is not None:
            name, schema = p
            instance = kwargs[name]
            jsonschema.validate(instance=instance, schema=schema)

        result = endpoint_func(**kwargs)

        #        if result.content_type == "application/json"
        parsed_result = json.loads(result.data.decode("utf8"))

        response_schema = get_response_schema(endpoint)
        # assert response_schema is not None, "No response schema for {}".format(endpoint_func.__name__)
        if response_schema is not None:
            try:
                jsonschema.validate(instance=parsed_result, schema=response_schema)
            except:
                log.error(
                    "Got error trying to validate {}".format(endpoint_func.__name__)
                )
                raise

        return result

    return execute_with_validation
