def test_resolve_to_dataset(db_session):
    db = db_session.db

    dataset_version_id = create_dataset(db_session, shortname="short")
    dataset_id = db.get_dataset_version(dataset_version_id)['dataset_id']

    assert dataset_id == db.resolve_to_dataset("short")
    assert dataset_id == db.resolve_to_dataset(dataset_id)
    assert db.resolve_to_dataset("missing") is None

def test_resolve_to_dataset_version(db_session):
    db = db_session.db

    dataset_version_id = create_dataset(db_session, shortname="short", versions=2)
    dataset_id = db.get_dataset_version(dataset_version_id)['dataset_id']

    assert dataset_version_id == db.resolve_to_dataset_version("short")
    assert dataset_version_id == db.resolve_to_dataset_version(dataset_id)
    assert dataset_version_id == db.resolve_to_dataset_version(dataset_version_id)
    assert dataset_version_id == db.resolve_to_dataset_version("short:2")
    assert db.resolve_to_dataset_version("missing") is None

@pytest.mark.skip(reason="resolve_to_dataset returns object")
def test_resolve_to_datafile(db_session):
    db = db_session.db

    dataset_id = create_dataset(db_session, shortname="short", versions=2, filenames=["file"])
    dataset_id = db.get_dataset_version(dataset_version_id)['dataset_id']

    assert (dataset_version_id, "file") == db.resolve_to_dataset_version("short")
    assert (dataset_version_id, "file") == db.resolve_to_dataset_version(dataset_id)
    assert (dataset_version_id, "file") == db.resolve_to_dataset_version(dataset_version_id)
    assert (dataset_version_id, "file") == db.resolve_to_dataset_version("short:1")
    assert (dataset_version_id, "file") == db.resolve_to_dataset_version("short/file")
    assert (dataset_version_id, "file") == db.resolve_to_dataset_version("short:1/file")
    assert db.resolve_to_dataset_version("missing") is None
