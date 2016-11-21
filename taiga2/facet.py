import attr
import json
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

    def project(self, data):
        "Return a projection of the data that satifies this facet's schema.  Only has defined behavior if is_valid returns true"
        p = {}
        for prop in self.properties:
            if prop.name in data:
                value = data[prop.name]
                p[prop.name] = prop.type.project(value)
            else:
                p[prop.name] = prop.type.default_value

        return p

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

    default_value = ""

    def is_value_valid(self, value):
        return isinstance(value, str) and (self.max_length is None or len(value) < self.max_length)

    def project(self, value):
        return value

@attr.s
class Number:
#    min = attr.ib(default=None)
#    max = attr.ib(default=None)
    format = attr.ib(default="%f")

    default_value = None

    def is_value_valid(self, value):
        return isinstance(value, float) 

    def project(self, value):
        return value

@attr.s
class Enum:
    values = attr.ib()
    is_collection = attr.ib(default=False) 
    allow_additions = attr.ib(default=False)

    default_value = None

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

    def project(self, value):
        return value

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
    # defining and updating facet are both immediate operations, however, they are created initially with a 
    # status of "pending".  After query has completed and facet specific table has been materialized, only then 
    # does the fact become "ready" and the facet_id can be used by queries  
    # extra complication: must not block edits which happen in parallel with materialization of facet.
    # The assumption is that writes are relatively infrequent relative to queries.
    # Should an query in parallel with an update return old date?  
    # perhaps best thinking of facet definitions as immutable, where an update creates a new materialized
    # version and then swaps in the new and drops the old.   Means creating a facet is as expensive as an update
    # will require a large sweep/copy many records to new view.
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

        # need to see if this matches any existing facets
        # and add to the approriate materialized views

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

        # need to see if this matches any existing facets
        # remove from existing previous views and re-add to new views 

    def delete_record(self, id):
        del self.records[id]

    def get_record(self, id):
        return deepcopy(self.records[id])

    # query API
    def find_by_facet(self, facet_def):
        # relatively slow because evaluated over full dataset and not just a facet
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

        records = [ record for record in records if matches_filter(record) ]

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

import requests

ES_ADDR="http://localhost:9200"

@attr.s
class FacetTransform:
    es_index_name = attr.ib()
    facet_def = attr.ib()

    def _update_doc(self, id, doc):
        c = requests.post(ES_ADDR+"/"+self.es_index_name+"/t/"+id, data=json.dumps(doc))
        assert c.status_code == 200, "status_code=%s, content=%s" % (c.status_code, c.content)

    def _delete_doc(self, id):
        c = requests.delete(ES_ADDR+"/"+self.es_index_name+"/t/"+id)
        assert c.status_code == 200, "status_code=%s, content=%s" % (c.status_code, c.content)

    def process(self, id, doc):
        if doc is None:
            self._delete_doc(id)
        else:
            if self.facet_def.is_valid(doc):
                projected = self.facet_def.project(doc)
                self._update_doc(id, projected)
            else:
                print("doc is invalid", doc)

@attr.s
class ESQuery:
    es_index_name = attr.ib()

    def query(self):
        # this doesn't work.  Why?
        c = requests.post(ES_ADDR+"/"+self.es_index_name+"/_search?pretty", data=json.dumps({"query": { "match_all": {} }}))
        assert c.status_code == 200, "status_code=%s, content=%s" % (c.status_code, c.content.decode('utf8'))
        print(c.content.decode("utf8"))

@attr.s
class FacetConf:
    name = attr.ib()
    # one of: building, update-building, update-ready, availible
    status = attr.ib()
    # an instance of FacetTransform
    current_def = attr.ib()
    # an instance of FacetTransform or None
    next_def = attr.ib()


class ESPush:
    def __init__(self, facet_transforms):
        self.facet_transforms = facet_transforms

    def update_with_doc(self, id, doc):
        for t in self.facet_transforms:
            t.process(id, doc)

if __name__ == "__main__":
    user_def = FacetDef(properties = [
        Property(name = "name",
            required = True,
            type = String()),

        Property(name = "access",
            required = True,
            type = Enum(values = [
                EnumValue("user", "user"),
                EnumValue("admin", "admin"),
            ])),
        
        Property(name = "email",
            required = False,
            type = String()),
        ])
    
    transform = FacetTransform("testindex", user_def)
    esp = ESPush([transform])
    esp.update_with_doc("10", dict(name="joe", access="user", email="foo@sample.com"))
    esq = ESQuery("testindex")
    esq.query()
