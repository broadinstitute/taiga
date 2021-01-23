from taiga2.schemas import ma, FolderNamedIdSchema, EntrySchema, FolderNamedIdSchema


class BreadcrumbSchema(ma.ModelSchema):
    class Meta:
        additional = ("order",)

    folder = ma.Nested(FolderNamedIdSchema)


class SearchEntrySchema(ma.ModelSchema):
    entry = ma.Nested(EntrySchema)
    breadcrumbs = ma.Nested(BreadcrumbSchema, many=True)


class SearchResultSchema(ma.ModelSchema):
    class Meta:
        additional = ("name",)

    current_folder = ma.Nested(FolderNamedIdSchema)
    entries = ma.Nested(SearchEntrySchema, many=True)
