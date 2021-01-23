import flask

from taiga2.controllers.endpoint_validation import validate

from taiga2.activities.models import Activity
from taiga2.activities.schemas import ActivityLogSchema


@validate
def get_activity_log_for_dataset_id(datasetId: str):
    array_activity_log = Activity.get_by(dataset_id=datasetId)

    activity_log_schema = ActivityLogSchema(many=True)
    json_data_access_logs_entry = activity_log_schema.dump(array_activity_log).data

    return flask.jsonify(json_data_access_logs_entry)
