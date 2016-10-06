Do I need a more compeling example set of folders for demoing?

todo:
    - consistent UI for updating/complete/error
    - implement set state (delete/deprecate/valid)
    - FolderView 
        - Add access summary ("public", vs "shared", vs "private")
        - add folder description/name update to swagger and default controller
    - DatasetView
        - (x) Show permnames
        - Highlight current version
        - Add support for rendering description
        - version status (delete/deprecate/valid)
        - code snippets for how to fetch this dataset
    - Provenance
        - api endpoint for setProvenance(dataset_version_id, method, input_data_files)
        - dataset's provenance returned in dataset version response.   Also return list of 
          datasets derived from this one?
    - Modal dialogs for:
        - dest folder selection (used by "move" and "copy")
        - (x) edit name (Used by both dataset and folder)
        - (x) edit description
        - create folder (Reuse edit name?) 
        - edit ACL
        - edit provenance
    - ACL support
        - acl on every folder and dataset
        - new folders and new datasets copy acl from the folder they're created into
        - acls are lists of form (entity, permission)
            - entity = { user | group | everyone }
            - permission = read | read-write | owner
            - acls only add permissions, no exclusions, so order of processing doesn't matter
            - on all operations call has_permission(acl, user, permission)
        - new api end points for defining groups (CRUD)
    - new pages for
        - create new dataversion (unclear what that should look like)
            - Load from an existing bucket?  Good first pass because avoids needing upload.            
        - show dataset activity
