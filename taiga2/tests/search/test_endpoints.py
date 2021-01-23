from flask_sqlalchemy import SessionBase

import taiga2.controllers.models_controller as models_controller
from taiga2.search.endpoints import search_within_folder

from taiga2.tests.test_endpoint import (
    new_dataset_in_new_folder_in_home,
    get_data_from_flask_jsonify,
    new_folder_in_home,
    new_datafile,
)


def test_search_within_folder(session: SessionBase, new_dataset_in_new_folder_in_home):
    current_user = models_controller.get_current_session_user()
    home_folder_id = current_user.home_folder_id
    search_query = "New Dataset in a folder"
    r = get_data_from_flask_jsonify(search_within_folder(home_folder_id, search_query))
    assert r["current_folder"]["id"] == home_folder_id
    assert len(r["entries"]) == 1
    assert r["entries"][0]["entry"]["id"] == new_dataset_in_new_folder_in_home.id
