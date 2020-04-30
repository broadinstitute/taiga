from typing import List

from flask import current_app, url_for
from mailjet_rest import Client

from taiga2.controllers import models_controller
from taiga2.models import DatasetSubscription


def send_emails_for_dataset(dataset_id: str, version_author_id: str):
    dataset = models_controller.get_dataset(dataset_id, True)
    dataset_subscriptions = (
        dataset.dataset_subscriptions
    )  # type: List[DatasetSubscription]

    # Don't email the person who just updated the dataset
    dataset_subscribers = [
        ds.user
        for ds in dataset_subscriptions
        if ds.user.email is not None and ds.user.id != version_author_id
    ]
    if len(dataset_subscribers) == 0:
        return

    mailjet = Client(
        auth=(
            current_app.config["MAILJET_API_KEY"],
            current_app.config["MAILJET_SECRET"],
        ),
        version="v3.1",
    )

    dataset_url = "https://cds.team/taiga/dataset/{}".format(dataset.permaname)

    data = {
        "Messages": [
            {
                "From": {"Email": current_app.config["MAILJET_EMAIL"]},
                "To": [{"Email": user.email}],
                "Subject": "Taiga Dataset Updated - {}".format(dataset.name),
                "TextPart": "Hello,\n"
                + "Someone has created a new version of the Taiga dataset {}. See the new version here: {}\n".format(
                    dataset.name, dataset_url
                )
                + 'To unsubscribe from updates about this dataset, click the "unsubscribe" button on the page linked above.',
            }
            for user in dataset_subscribers
        ]
    }
    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())
    return result
