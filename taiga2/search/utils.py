from typing import List, Collection

from taiga2.models import Folder
from taiga2.search.models import Breadcrumb, SearchEntry, SearchResult


def find_matching_name(
    root_folder: Folder, breadcrumbs: List[Breadcrumb], search_query: str
) -> List[SearchEntry]:
    matching_entries = []
    # Can't append on a copy()??
    local_breadcrumbs = breadcrumbs.copy()
    local_breadcrumbs.append(Breadcrumb(order=len(breadcrumbs) + 1, folder=root_folder))

    for entry in root_folder.entries:
        if search_query.lower() in entry.name.lower():
            search_entry = SearchEntry(entry=entry, breadcrumbs=local_breadcrumbs)
            matching_entries.append(search_entry)

        # If this is a folder, we enter into it and search inside it
        if isinstance(entry, Folder):
            # We need to be mindful about the same folder being in itself => Infinite recursion
            already_in = any(
                [breadcrumb.folder.id == entry.id for breadcrumb in local_breadcrumbs]
            )

            if not already_in:
                matching_entries.extend(
                    find_matching_name(entry, local_breadcrumbs, search_query)
                )

    return matching_entries
