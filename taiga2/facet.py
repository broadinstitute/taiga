import attr

@attr.s
class NamedFacet:
    name = attr.ib()
    definition = attr.ib()

@attr.s
class FacetDef:
    properties = attr.ib()

    @property
    def required_properties():
        return [p for p in self.properties if p.required]

    def is_valid(self, data):
        for prop in self.properties:
            if prop.name not in data:
                if prop.required:
                    return False
                else:
                    continue

            value = data[prop.name]
            if not prop.type.is_value_valid(value):
                return False

        return True

@attr.s
class Property:
    name = attr.ib()
    required = attr.ib()
    type = attr.ib()
    display_as = attr.ib(default=None)

@attr.s
class String:
    expected_length = attr.ib(default=50)
    expected_lines = attr.ib(default=1)
    max_length = attr.ib(default=None)

    def is_value_valid(self, value):
        return isinstance(value, str) and (self.max_length is None or len(value) < self.max_length)

@attr.s
class Number:
#    min = attr.ib(default=None)
#    max = attr.ib(default=None)
    format = attr.ib(default="%f")

    def is_value_valid(self, value):
        return isinstance(value, float) 

@attr.s
class Enum:
    values = attr.ib()
    is_collection = attr.ib(default=False) 
    allow_additions = attr.ib(default=False)

    def is_value_valid(self, value):
        valid_values = set([v.value for v in self.values])
        if self.is_collection:
            if not isinstance(value, list):
                return False
            for v in value:
                if not (isinstance(v, str) and v in valid_values):
                    return False
            return True
        else:
            return isinstance(value, str) and value in valid_values

@attr.s
class EnumValue:
    value = attr.ib()
    label = attr.ib(default=None)

@attr.s
class Record:
    id = attr.ib()
    properties = attr.ib()


import collections
from copy import deepcopy
class MockDB:
    def __init__(self):
        self.records = {}
        self.facets = {}
        self.next_id = 0

    # facet CRUD
    def define_facet(self, name, facet_def):
        assert isinstance(facet_def, FacetDef)
        id = self.next_id
        self.next_id += 1
        self.facets[id] = NamedFacet(name, facet_def)
        return id

    def update_facet(self, id, name, facet_def):
        assert isinstance(facet_def, FacetDef)
        assert id in self.facets
        self.facets[id] = NamedFacet(name, facet_def)

    def get_facet(self, id):
        return self.facets[id]

    # record CRUD
    def insert_record(self, record, facet_id):
        if facet_id is not None:
            facet = self.get_facet(facet_id)
            assert facet.definition.is_valid(record)

        id = self.next_id
        self.next_id += 1
        self.records[id] = record

    def update_record(self, id, key_values, facet_id):
        record = deepcopy(self.records[id])
        for k, v in key_values:
            if v is None:
                del record[k]
            else:
                record[k] = v

        if facet_id is not None:
            facet = self.get_facet(facet_id)
            assert facet.definition.is_valid(record)

        self.records[id] = record

    def delete_record(self, id):
        del self.records[id]

    def get_record(self, id):
        return deepcopy(self.records[id])

    # query API
    def find_by_facet(self, facet_def):
        return [Record(id, record) for id, record in self.records.items() if facet_def.is_valid(record)]

    def find_by_facet_id(self, facet_id, filters, include_subfacet_summary):
        facet = self.get_facet(facet_id)
        records = self.find_by_facet(facet.definition)
        
        def matches_filter(record):
            for filter_prop, filter_value in filters.items():
                record_value = record.properties.get(filter_prop)
                if filter_value != record_value:
                    return False
            return True

        records = [ record in records if matches_filter(record) ]

        if include_subfacet_summary:
            summary = self._summarize_subfacets(records)
        else:
            summary = None

        return (records, summary)

    def _summarize_subfacets(self, records):
        by_prop_value = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        for record in records:
            # does not handle multiple values correctly
            for k, v in record.properties.items():
                by_prop_value[k][v] += 1
        return by_prop_value

