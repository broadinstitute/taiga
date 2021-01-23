from typing import List

from taiga2.models import Entry, Folder


class Breadcrumb:
    """Object tracking the path we took to find a specific entry when performing a search
    Should contain the entry (folder) we pass through, and its order
    """

    def __init__(self, order: int, folder: Folder):
        self.order = order
        self.folder = folder


class SearchEntry:
    """Object resulting from a search.
    Should contain the entry found and breadcrumbs (path to reach the entry)
    """

    def __init__(self, entry: Entry, breadcrumbs: List[Breadcrumb]):
        self.entry = entry
        self.breadcrumbs = breadcrumbs


class SearchResult:
    """Container object of a search.
    Should contain the root folder we search from, the name of the search and the entries fetched from the search
    """

    def __init__(self, current_folder: Folder, name: str, entries: List[SearchEntry]):
        self.current_folder = current_folder
        self.name = name
        self.entries = entries
