from typing import List

import flask

from taiga2.controllers.endpoint_validation import validate
import taiga2.controllers.models_controller as mc

from taiga2.search.models import SearchResult, Breadcrumb
from taiga2.search.schemas import SearchResultSchema
from taiga2.search.utils import find_matching_name


@validate
def search_within_folder(current_folder_id: str, search_query: str):
    """Given a folder id and a search query (string), will return all the datasets and folders that are matching the query inside the folder
    """
    # Get the folder
    folder = mc.get_folder(current_folder_id, one_or_none=True)
    if folder is None:
        flask.abort(404)

    # Search inside the folder
    breadcrumbs: List[Breadcrumb] = []
    all_matching_entries = find_matching_name(
        root_folder=folder, breadcrumbs=breadcrumbs, search_query=search_query
    )

    # TODO: Should also encapsulate this search to return a SearchResult we ask Marshmallow to jsonify
    search_name = "Search results for " + search_query + " within " + folder.name
    search_result = SearchResult(
        current_folder=folder, name=search_name, entries=all_matching_entries
    )

    search_result_schema = SearchResultSchema()
    result = search_result_schema.dump(search_result).data

    return flask.jsonify(result)
