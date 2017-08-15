import json


def get_dict_from_response_jsonify(jsonified_response):
    """Utils function to get a dict from a Response built with flask.jsonify"""
    return json.loads(jsonified_response.get_data(as_text=True))
