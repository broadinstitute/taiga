import flask

from taiga2.controllers.endpoint_validation import validate
import taiga2.controllers.models_controller as mc
from taiga2.extensions import db
from taiga2.subscriptions.models import DatasetSubscription


@validate
def add_dataset_subscription(dataset_id: str):
    """Subscribes the current user to dataset with id dataset_id"""
    current_user = mc.get_current_session_user()
    subscription, is_new = DatasetSubscription.get_or_create(
        dataset_id=dataset_id, user_id=current_user.id
    )
    if is_new:
        db.session.commit()
        return flask.make_response(flask.jsonify(subscription.id), 201)
    return flask.jsonify(subscription.id)


@validate
def delete_dataset_subscription(subscription_id: str):
    """Unsubscribes the current user to dataset with id dataset_id"""
    current_user = mc.get_current_session_user()
    subscription = DatasetSubscription.get(subscription_id)

    if subscription is None:
        flask.abort(404)

    subscription.delete()
    db.session.commit()

    return flask.jsonify(True)
