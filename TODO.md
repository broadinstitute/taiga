## Do I need a more compelling example set of folders for demoing?

Todo:

  - [ ] Consistent UI for updating/complete/error
  - [ ] Implement set state (delete/deprecate/valid)
  - FolderView 
      - [ ] Add access summary ("public", vs "shared", vs "private")
      - [ ] Add folder description/name update to swagger and default controller
  - DatasetView
      - [x] Show permnames
      - [ ] Highlight current version
      - [ ] Add support for rendering description
      - [ ] Version status (delete/deprecate/valid)
      - [ ] Code snippets for how to fetch this dataset
  - Provenance
      - [ ] Api endpoint for setProvenance(dataset_version_id, method, input_data_files)
      - [ ] Dataset's provenance returned in dataset version response.   Also return list of 
        datasets derived from this one?
  - Modal dialogs for:
      - [ ] Dest folder selection (used by "move" and "copy")
      - [x] Edit name (Used by both dataset and folder)
      - [x] Edit description
      - [ ] Create folder (Reuse edit name?) 
      - [ ] Edit ACL
      - [ ] Edit provenance
  - ACL support
      - [ ] Acl on every folder and dataset
      - [ ] New folders and new datasets copy acl from the folder they're created into
      - [ ] Acls are lists of form (entity, permission)
          - [ ] Entity = { user | group | everyone }
          - [ ] Permission = read | read-write | owner
          - [ ] Acls only add permissions, no exclusions, so order of processing doesn't matter
          - [ ] On all operations call has_permission(acl, user, permission)
      - [ ] New api end points for defining groups (CRUD)
  - New pages for
      - [ ] Create new data version (unclear what that should look like)
          - [ ] Load from an existing bucket?  Good first pass because avoids needing upload.
      - [ ] Show dataset activity
