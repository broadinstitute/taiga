import flask
import json
import pytest

from flask_sqlalchemy import SessionBase
import werkzeug.exceptions

import taiga2.controllers.endpoint as endpoint
import taiga2.controllers.models_controller as models_controller

from taiga2.models import generate_permaname, S3DataFile, Dataset, DatasetVersion
from taiga2.tests.test_utils import get_dict_from_response_jsonify


# <editor-fold desc="Fixtures and utils">


@pytest.fixture
def new_user():
    user_name = "new user"
    user_email = "new_user@email.com"
    _new_user = models_controller.add_user(name=user_name, email=user_email)
    return _new_user


@pytest.fixture
def new_upload_session():
    response_json_new_upload_session_id = endpoint.create_new_upload_session()
    new_upload_session_id = get_data_from_flask_jsonify(
        response_json_new_upload_session_id
    )
    return models_controller.get_upload_session(new_upload_session_id)


def _add_s3_file_to_upload_session(
    sid, bucket="test_bucket", format="Raw", file_name="filekey", encoding=None
):
    key = file_name

    uploadMetadata = {
        "filename": file_name,
        "filetype": "s3",
        "s3Upload": {"bucket": bucket, "format": format, "key": key},
    }

    if encoding is not None:
        uploadMetadata["s3Upload"]["encoding"] = encoding

    endpoint.create_upload_session_file(uploadMetadata=uploadMetadata, sid=sid)

    _new_upload_session_files = models_controller.get_upload_session_files_from_session(
        sid
    )

    return _new_upload_session_files[0]


def _add_virtual_file_to_upload_session(
    sid, name="name", taiga_id=None, datafile_id=None
):
    assert taiga_id is not None or datafile_id is not None

    if taiga_id is None:
        datafile = DataFile.query.get(datafile_id)
        assert datafile is not None
        taiga_id = "{}.{}/{}".format(
            datafile.dataset_version.dataset.permaname,
            datafile.dataset_version.version,
            datafile.name,
        )

    uploadMetadata = {
        "filename": name,
        "filetype": "virtual",
        "existingTaigaId": taiga_id,
    }

    endpoint.create_upload_session_file(uploadMetadata=uploadMetadata, sid=sid)

    _new_upload_session_files = models_controller.get_upload_session_files_from_session(
        sid
    )

    return _new_upload_session_files[0]


@pytest.fixture
def new_upload_session_file(session: SessionBase, new_upload_session):
    return _add_s3_file_to_upload_session(new_upload_session.id)


@pytest.fixture
def new_datafile():
    # TODO: These tests should be using the endpoint and not the model
    new_datafile_name = "New Datafile"

    _new_datafile = models_controller.add_s3_datafile(
        name=new_datafile_name,
        s3_bucket="broadtaiga2prototype",
        s3_key=models_controller.generate_convert_key(),
        compressed_s3_key=models_controller.generate_compressed_key(),
        type=S3DataFile.DataFileFormat.Raw,
        encoding="UTF-8",
        short_summary="short",
        long_summary="long",
    )

    return _new_datafile


@pytest.fixture
def new_dataset(new_datafile):
    # TODO: These tests should be using the endpoint and not the model
    new_dataset_name = "New Dataset"
    new_dataset_permaname = generate_permaname(new_dataset_name)

    _new_dataset = models_controller.add_dataset(
        name=new_dataset_name,
        permaname=new_dataset_permaname,
        description="New dataset description",
        datafiles_ids=[new_datafile.id],
    )

    return _new_dataset


@pytest.fixture
def dataset_create_access_log(session: SessionBase, new_dataset):
    endpoint.create_or_update_entry_access_log(new_dataset.id)
    return new_dataset


@pytest.fixture
def new_folder_in_home(session: SessionBase):
    current_user = models_controller.get_current_session_user()
    home_folder_id = current_user.home_folder_id
    metadata = {
        "name": "New folder in home",
        "description": "Folder to create a folder inside a folder",
        "parentId": home_folder_id,
    }
    new_folder_json = endpoint.create_folder(metadata)
    new_folder_id = json.loads(new_folder_json.get_data(as_text=True))["id"]
    _new_folder = models_controller.get_entry(new_folder_id)
    return _new_folder


@pytest.fixture(scope="function")
def new_dataset_in_new_folder_in_home(
    session: SessionBase, new_folder_in_home, new_datafile
):
    new_dataset_name = "New Dataset in a folder"
    new_dataset_permaname = generate_permaname(new_dataset_name)

    _new_dataset = models_controller.add_dataset(
        name=new_dataset_name,
        permaname=new_dataset_permaname,
        description="New dataset description",
        datafiles_ids=[new_datafile.id],
    )

    models_controller.move_to_folder([_new_dataset.id], None, new_folder_in_home.id)

    return _new_dataset


def get_data_from_flask_jsonify(flask_jsonified):
    return flask.json.loads(flask_jsonified.data.decode("UTF8"))


def test_endpoint_s3_credentials(app, session: SessionBase):
    dict_credentials = endpoint.get_s3_credentials()
    # TODO: Assert the dict content


def test_create_new_upload_session(session: SessionBase):
    response_json_new_upload_session_id = endpoint.create_new_upload_session()
    new_upload_session_id = get_data_from_flask_jsonify(
        response_json_new_upload_session_id
    )
    assert models_controller.get_upload_session(new_upload_session_id) is not None


def test_create_upload_session_file(app, session: SessionBase, new_upload_session):
    bucket = "test_bucket"
    format = "Raw"
    file_key = "filekey"
    file_name = file_key

    uploadMetadata = {
        "filename": file_name,
        "filetype": "s3",
        "s3Upload": {"bucket": bucket, "format": format, "key": file_key},
    }

    sid = new_upload_session.id

    response_json_create_upload_session_file = endpoint.create_upload_session_file(
        uploadMetadata=uploadMetadata, sid=sid
    )
    task_id = get_data_from_flask_jsonify(response_json_create_upload_session_file)

    assert task_id is not None

    # Verify we have now a new upload session file in db
    _new_upload_session_files = models_controller.get_upload_session_files_from_session(
        sid
    )

    assert len(_new_upload_session_files) == 1
    assert _new_upload_session_files[0].filename == file_name


def test_create_dataset(session: SessionBase, new_upload_session_file):
    _new_upload_session_id = new_upload_session_file.session.id

    models_controller.update_upload_session_file_summaries(
        new_upload_session_file.id,
        "short_summary_test",
        "long_summary_test",
        None,
        None,
        None,
    )

    dataset_name = "Dataset Name"
    dataset_description = "Dataset Description"

    home_folder_id = models_controller.get_current_session_user().home_folder.id

    sessionDatasetInfo = {
        "sessionId": _new_upload_session_id,
        "datasetName": dataset_name,
        "datasetDescription": dataset_description,
        "currentFolderId": home_folder_id,
    }
    response_json_create_dataset = endpoint.create_dataset(
        sessionDatasetInfo=sessionDatasetInfo
    )
    _new_dataset_id = get_data_from_flask_jsonify(response_json_create_dataset)

    assert _new_dataset_id is not None

    _new_dataset = models_controller.get_dataset(_new_dataset_id)

    assert _new_dataset.name == dataset_name
    datafile = _new_dataset.dataset_versions[0].datafiles[0]
    assert datafile.name == new_upload_session_file.filename
    assert datafile.short_summary == "short_summary_test"
    assert datafile.long_summary == "long_summary_test"


def test_create_new_dataset_version(
    session: SessionBase, new_dataset, new_upload_session_file
):
    new_description = "My new description!"

    session_id = new_upload_session_file.session.id

    # TODO: Get instead the last datasetVersion
    latest_dataset_version = new_dataset.dataset_versions[0]

    # We fetch the datafiles from the first dataset_version
    assert len(latest_dataset_version.datafiles) == 1
    datafile = latest_dataset_version.datafiles[0]

    datasetVersionMetadata = {
        "sessionId": session_id,
        "datasetId": new_dataset.id,
        "newDescription": new_description,
    }

    _add_virtual_file_to_upload_session(
        session_id, datafile.name, datafile_id=datafile.id
    )

    response_json_create_new_dataset_version_id = endpoint.create_new_dataset_version(
        datasetVersionMetadata
    )
    new_dataset_version_id = get_data_from_flask_jsonify(
        response_json_create_new_dataset_version_id
    )

    _new_dataset_version = models_controller.get_dataset_version(new_dataset_version_id)

    assert _new_dataset_version.version == latest_dataset_version.version + 1
    # TODO: Test the number of uploaded files in the session + the 1 existing file
    assert len(_new_dataset_version.datafiles) == 2

    assert _new_dataset_version.description == new_description
    # TODO: Check if the datafiles in the new dataset_version are the same (filename/name) than in the new_upload_session_file + in the previous_dataset_version_datafiles


def test_get_dataset_version_from_dataset(session: SessionBase, new_dataset):
    dataset_version_id = new_dataset.dataset_versions[0].id

    # test fetch by dataset version id
    # passing dataset in as "x" because it is unused and using that assumption when making urls in taiga1 redirect and taigr and taigapy
    dv = get_data_from_flask_jsonify(
        endpoint.get_dataset_version_from_dataset("x", dataset_version_id)
    )
    assert dv["datasetVersion"]["id"] == dataset_version_id

    # test alternative mode where we provide a permaname and a version
    dv = get_data_from_flask_jsonify(
        endpoint.get_dataset_version_from_dataset(new_dataset.permaname, "1")
    )
    assert dv["datasetVersion"]["id"] == dataset_version_id
    for df in dv["datasetVersion"]["datafiles"]:
        assert df["type"] == "Raw"

    # test fetching non-existant dataset results in 404
    with pytest.raises(werkzeug.exceptions.NotFound):
        endpoint.get_dataset_version_from_dataset("invalid", "invalid")


def test_get_dataset_two_ways(session: SessionBase, new_dataset):
    import werkzeug.exceptions

    dataset_id = new_dataset.id

    # test fetch by dataset version id
    # passing dataset in as "x" because it is unused and using that assumption when making urls in taiga1 redirect and taigr and taigapy
    ds = get_data_from_flask_jsonify(endpoint.get_dataset(dataset_id))
    assert ds["id"] == dataset_id

    # test alternative mode where we provide a permaname and a version
    ds = get_data_from_flask_jsonify(endpoint.get_dataset(dataset_id))
    assert ds["id"] == dataset_id

    # test fetching non-existant dataset results in 404
    with pytest.raises(werkzeug.exceptions.NotFound):
        endpoint.get_dataset("invalid")


def test_get_dataset_permaname(session: SessionBase, new_dataset: Dataset):
    ds = get_data_from_flask_jsonify(endpoint.get_dataset(new_dataset.permaname))

    assert ds["permanames"][0] == new_dataset.permaname
    assert ds["id"] == new_dataset.id


def test_deprecate_dataset_version(session: SessionBase, new_dataset: Dataset):
    """Check if deprecation was a success"""
    dataset_version_id = new_dataset.dataset_versions[0].id
    reason_state = "Test deprecation"
    deprecationReasonObj = {"deprecationReason": reason_state}

    flask_answer = endpoint.deprecate_dataset_version(
        dataset_version_id, deprecationReasonObj=deprecationReasonObj
    )
    ack = get_data_from_flask_jsonify(flask_answer)

    updated_dataset_version = models_controller.get_dataset_version(dataset_version_id)

    assert (
        updated_dataset_version.state == DatasetVersion.DatasetVersionState.deprecated
    )
    assert updated_dataset_version.reason_state == reason_state


def test_error_deprecate_dataset_version(session: SessionBase, new_dataset: Dataset):
    dataset_version_id = new_dataset.dataset_versions[0].id
    reason_state = "Test deprecation"
    deprecationReasonObj = {"deprecationReason": reason_state}

    error_raised = False
    try:
        endpoint.deprecate_dataset_version(
            "", deprecationReasonObj=deprecationReasonObj
        )
    except:
        error_raised = True

    assert error_raised, "Error not raised despite no dataset_version id passed"

    error_raised = False
    try:
        endpoint.deprecate_dataset_version(
            dataset_version_id, deprecationReasonObj={"deprecationReason": None}
        )
    except:
        error_raised = True

    assert error_raised, "Error not raised despite no deprecation reason passed"


def test_de_deprecate_dataset_version(session: SessionBase, new_dataset: Dataset):
    # Deprecate the dataset version first
    dataset_version_id = new_dataset.dataset_versions[0].id
    models_controller.deprecate_dataset_version(
        dataset_version_id, "Test de-deprecation"
    )

    flask_answer = endpoint.de_deprecate_dataset_version(dataset_version_id)
    ack = get_data_from_flask_jsonify(flask_answer)

    updated_dataset_version = models_controller.get_dataset_version(dataset_version_id)

    assert updated_dataset_version.state == DatasetVersion.DatasetVersionState.approved
    assert updated_dataset_version.reason_state == "Test de-deprecation"


def test_error_de_deprecate_dataset_version(session: SessionBase, new_dataset: Dataset):
    # Deprecate the dataset version first
    dataset_version_id = new_dataset.dataset_versions[0].id
    models_controller.deprecate_dataset_version(
        dataset_version_id, "Test de-deprecation"
    )

    error_raised = False
    try:
        endpoint.de_deprecate_dataset_version("")
    except:
        error_raised = True

    assert error_raised, "Error not raised despite no dataset_version id passed"


def test_delete_dataset_version(session: SessionBase, new_dataset: Dataset):
    dataset_version = new_dataset.dataset_versions[0]
    endpoint.delete_dataset_version(dataset_version.id)

    assert dataset_version.state == DatasetVersion.DatasetVersionState.deleted


def test_de_delete_dataset_version(session: SessionBase, new_dataset: Dataset):
    dataset_version = new_dataset.dataset_versions[0]
    dataset_version_id = dataset_version.id

    deprecation_reason = "DeprecationReason"
    reason_obj_should_not_be = {"deprecationReason": "ShouldNotBeSet"}

    models_controller.deprecate_dataset_version(
        dataset_version_id=dataset_version_id, reason="DeprecationReason"
    )

    models_controller.delete_dataset_version(dataset_version_id=dataset_version_id)
    endpoint.deprecate_dataset_version(
        dataset_version_id, deprecationReasonObj=reason_obj_should_not_be
    )

    assert dataset_version.state == DatasetVersion.DatasetVersionState.deprecated
    assert dataset_version.reason_state == deprecation_reason


# <editor-fold desc="Access Logs">


def test_create_access_log(session: SessionBase, new_dataset):
    json_result = endpoint.create_or_update_entry_access_log(new_dataset.id)
    assert json_result.status_code == 200


def test_update_access_log(session: SessionBase, dataset_create_access_log):
    json_result = endpoint.create_or_update_entry_access_log(
        dataset_create_access_log.id
    )
    assert json_result.status_code == 200


def test_retrieve_user_access_log(session: SessionBase, dataset_create_access_log):
    entries_access_logs = get_dict_from_response_jsonify(
        endpoint.get_entries_access_logs()
    )
    assert entries_access_logs[0]["entry"]["id"] == dataset_create_access_log.id


# TODO: We should also test the time logged and verify it matches when we called it

# </editor-fold>

# <editor-fold desc="Provenance">


def test_import_provenance(session: SessionBase, new_dataset):
    datafile_from_dataset = new_dataset.dataset_versions[0].datafiles[0]
    node_id = models_controller.models.generate_permaname("node_name")
    provenanceData = {
        "name": "Test provenance",
        "graph": {
            "nodes": [
                {
                    "label": datafile_from_dataset.name,
                    "type": "dataset",
                    "datafile_id": datafile_from_dataset.id,
                    "id": node_id,
                }
            ],
            "edges": [{"from_id": node_id, "to_id": node_id}],
        },
    }

    response_graph_id = endpoint.import_provenance(provenanceData)
    new_graph_id = get_data_from_flask_jsonify(response_graph_id)

    assert new_graph_id

    new_graph = models_controller.get_provenance_graph_by_id(new_graph_id)
    assert len(new_graph.provenance_nodes) == 1

    new_node = models_controller.get_provenance_node(
        new_graph.provenance_nodes[0].node_id
    )
    assert new_node.datafile_id == datafile_from_dataset.id

    new_edge = models_controller.get_provenance_edge(new_node.from_edges[0].edge_id)
    assert new_edge.from_node == new_edge.to_node


# </editor-fold>

# <editor-fold desc="Security">


def test_no_parents_access(new_dataset_in_new_folder_in_home, new_user):
    """Check that a different user from the owner has no access to the parent's folders"""
    models_controller._change_connected_user(new_user)
    _dataset = new_dataset_in_new_folder_in_home
    parents = get_dict_from_response_jsonify(endpoint.get_dataset(_dataset.id))[
        "folders"
    ]
    assert len(parents) == 0


def test_parent_visited_access(
    new_folder_in_home, new_dataset_in_new_folder_in_home, new_user
):
    """Check that if not owner has visited the parent folder of dataset,
    we have it in the parents list of the dataset"""
    models_controller._change_connected_user(new_user)
    _dataset = new_dataset_in_new_folder_in_home
    _folder_in_home = new_folder_in_home

    # Update a log access on this folder
    endpoint.create_or_update_entry_access_log(_folder_in_home.id)

    # Retrieve the dataset, which should contains a parent now
    parents = get_dict_from_response_jsonify(endpoint.get_dataset(_dataset.id))[
        "folders"
    ]

    assert len(parents) == 1


def test_remove_entry_permission(
    new_folder_in_home, new_dataset_in_new_folder_in_home, new_user
):
    models_controller._change_connected_user(new_user)
    _dataset = new_dataset_in_new_folder_in_home
    _folder_in_home = new_folder_in_home

    # Update a log access on this folder
    endpoint.create_or_update_entry_access_log(_folder_in_home.id)

    access_logs = get_dict_from_response_jsonify(
        endpoint.get_entry_access_logs(_folder_in_home.id)
    )

    assert len(access_logs) > 0

    # TODO: We should not to have to format this
    formatted_access_logs = map(
        lambda access_log: {
            "entry_id": access_log["entry"]["id"],
            "user_id": access_log["user_id"],
        },
        access_logs,
    )

    endpoint.accessLogs_remove(accessLogsToRemove=formatted_access_logs)

    # Retrieve the dataset, which should not contain a parent anymore now
    parents = get_dict_from_response_jsonify(endpoint.get_dataset(_dataset.id))[
        "folders"
    ]

    assert len(parents) == 0


# </editor-fold>


def _create_dataset_with_a_file(name="datafile") -> Dataset:
    _new_datafile = models_controller.add_s3_datafile(
        name=name,
        s3_bucket="broadtaiga2prototype",
        s3_key=models_controller.generate_convert_key(),
        compressed_s3_key=models_controller.generate_compressed_key(),
        type=models_controller.S3DataFile.DataFileFormat.Raw,
        encoding="UTF-8",
        short_summary="short",
        long_summary="long",
    )

    dataset = models_controller.add_dataset(
        name="dataset", description="", datafiles_ids=[_new_datafile.id]
    )

    return dataset


from taiga2.models import DataFile


def _create_dataset_with_a_virtual_file(
    files, folder_id, name="virtual", description="description"
) -> Dataset:
    datafiles = []
    for file in files:
        datafile = DataFile.query.get(file[1])
        assert datafile is not None
        datafiles.append(models_controller.add_virtual_datafile(file[0], datafile.id))

    dataset = models_controller.add_dataset(
        name=name, description=description, datafiles_ids=[x.id for x in datafiles]
    )

    models_controller.copy_to_folder([dataset.id], folder_id)

    return dataset


def test_dataset_endpoints_on_virtual_dataset(session: SessionBase):
    dataset1 = _create_dataset_with_a_file()
    data_file_1 = dataset1.dataset_versions[0].datafiles[0]
    data_file_1_label = "{}.1/datafile".format(dataset1.permaname)
    folder = models_controller.add_folder(
        "folder", models_controller.Folder.FolderType.folder, "folder desc"
    )
    folder_id = folder.id

    vdatafile_name = "alias"
    vdataset = _create_dataset_with_a_virtual_file(
        folder_id=folder_id, files=[(vdatafile_name, data_file_1.id)]
    )
    vdataset_id = vdataset.id

    folder_contents = get_data_from_flask_jsonify(endpoint.get_folder(folder.id))

    assert len(folder_contents["entries"]) == 1
    assert folder_contents["entries"][0]["type"] == "dataset"

    # verify that get_dataset accomodates virtual_dataset_ids the same as real datasets
    dataset = get_data_from_flask_jsonify(endpoint.get_dataset(vdataset_id))
    assert dataset["name"] == "virtual"
    assert len(dataset["versions"]) == 1

    vdataset_permaname = dataset["permanames"][0]
    vdataset_version_id = dataset["versions"][0]["id"]

    # verify get_datasets is also sane
    datasets = get_data_from_flask_jsonify(
        endpoint.get_datasets(dict(datasetIds=[vdataset_id]))
    )
    assert len(datasets) == 1

    # make sure we can get it by permaname too
    dataset = get_data_from_flask_jsonify(endpoint.get_dataset(vdataset_permaname))
    assert dataset["name"] == "virtual"
    assert len(dataset["versions"]) == 1

    # run through all the dataset endpoints and just make sure we don't get any exceptions
    get_data_from_flask_jsonify(endpoint.get_dataset_last(vdataset_id))
    get_data_from_flask_jsonify(
        endpoint.update_dataset_name(vdataset_id, {"name": "new name"})
    )
    get_data_from_flask_jsonify(
        endpoint.update_dataset_description(
            vdataset_id, {"description": "new description"}
        )
    )
    dataset_version = get_data_from_flask_jsonify(
        endpoint.get_dataset_version(vdataset_version_id)
    )
    assert len(dataset_version["datafiles"]) == 1
    datafile = dataset_version["datafiles"][0]
    assert datafile["name"] == vdatafile_name
    assert datafile["type"] == "Raw"
    assert datafile["underlying_file_id"] == data_file_1_label

    # skipping get_dataset_versions because I don't know what uses it
    # endpoint.get_dataset_versions()
    get_data_from_flask_jsonify(
        endpoint.get_dataset_version_from_dataset(vdataset_id, vdataset_version_id)
    )
    get_data_from_flask_jsonify(
        endpoint.update_dataset_version_description(
            vdataset_version_id, {"description": "new description"}
        )
    )
    get_data_from_flask_jsonify(
        endpoint.deprecate_dataset_version(
            vdataset_version_id, {"deprecationReason": "reason"}
        )
    )
    get_data_from_flask_jsonify(
        endpoint.de_deprecate_dataset_version(vdataset_version_id)
    )
    get_data_from_flask_jsonify(endpoint.delete_dataset_version(vdataset_version_id))
    get_data_from_flask_jsonify(endpoint.de_delete_dataset_version(vdataset_version_id))

    version = 1
    format = "raw"
    get_data_from_flask_jsonify(
        endpoint.get_datafile(
            format, dataset_version_id=vdataset_version_id, datafile_name=vdatafile_name
        )
    )
    get_data_from_flask_jsonify(
        endpoint.get_datafile(
            format,
            dataset_permaname=vdataset_permaname,
            version=version,
            datafile_name=vdatafile_name,
        )
    )
    get_data_from_flask_jsonify(
        endpoint.get_datafile_short_summary(
            dataset_permaname=vdataset_permaname,
            version=version,
            datafile_name=vdatafile_name,
        )
    )
    get_data_from_flask_jsonify(endpoint.search_within_folder(folder_id, "description"))

    folder2 = models_controller.add_folder(
        "folder2", models_controller.Folder.FolderType.folder, "folder desc"
    )
    get_data_from_flask_jsonify(
        endpoint.move_to_folder(
            dict(
                entryIds=[vdataset_id],
                currentFolderId=folder_id,
                targetFolderId=folder2.id,
            )
        )
    )

    # TODO: Do we need to cover these? Currently not working but I don't know what these are actually used for
    # get_data_from_flask_jsonify(endpoint.create_or_update_dataset_access_log(vdataset_id))


def create_session_with_virtual(new_name, old_name):
    uploadSessionFile = {
        "filename": new_name,
        "filetype": "virtual",
        "existingTaigaID": old_name,
    }

    sid = new_upload_session.id

    endpoint.create_upload_session_file(uploadSessionFile=uploadSessionFile, sid=sid)
    _new_upload_session_files = models_controller.get_upload_session_files_from_session(
        sid
    )
    return _new_upload_session_files[0]


def test_create_virtual_dataset_endpoint(session: SessionBase):
    folder = models_controller.add_folder(
        "folder", models_controller.Folder.FolderType.folder, "folder desc"
    )

    dataset1 = _create_dataset_with_a_file("datafile")
    data_file_1 = "{}.1/datafile".format(dataset1.permaname)

    session.flush()

    upload_session_1 = new_upload_session()
    _add_virtual_file_to_upload_session(upload_session_1.id, "alias", data_file_1)

    sessionDatasetInfo = {
        "sessionId": upload_session_1.id,
        "datasetName": "version-1-name",
        "datasetDescription": "version-1-desc",
        "currentFolderId": folder.id,
    }

    response_json_create_dataset = endpoint.create_dataset(
        sessionDatasetInfo=sessionDatasetInfo
    )
    virtual_dataset_id = get_data_from_flask_jsonify(response_json_create_dataset)

    # versionInfo = {
    #     "description": "updated desc",
    #     "files": [
    #         {
    #             "name": "alias",
    #             "datafile": data_file_2
    #         }
    #     ]
    # }

    # now update with a new version
    upload_session_2 = new_upload_session()
    dataset2 = _create_dataset_with_a_file()
    data_file_2 = "{}.1/datafile".format(dataset2.permaname)
    _add_virtual_file_to_upload_session(upload_session_2.id, "alias", data_file_2)

    datasetVersionMetadata = {
        "sessionId": upload_session_2.id,
        "datasetId": virtual_dataset_id,
        "newDescription": "version-2-desc",
    }

    endpoint.create_new_dataset_version(datasetVersionMetadata=datasetVersionMetadata)

    v = models_controller.get_dataset(virtual_dataset_id)
    latest_dataset_version = models_controller.get_latest_dataset_version(v.id)
    assert v.name == "version-1-name"
    assert v.description == None
    assert latest_dataset_version.description == "version-2-desc"

    assert len(v.dataset_versions) == 2

    # check each version
    version = v.dataset_versions[0]
    assert version.version == 1
    assert len(version.datafiles) == 1
    entry = version.datafiles[0]
    assert entry.name == "alias"
    data_file_id_1 = entry.underlying_file_id

    version = v.dataset_versions[1]
    assert version.version == 2
    assert len(version.datafiles) == 1
    entry = version.datafiles[0]
    assert entry.name == "alias"
    assert entry.underlying_file_id != data_file_id_1


def test_search_within_folder(session: SessionBase, new_dataset_in_new_folder_in_home):
    current_user = models_controller.get_current_session_user()
    home_folder_id = current_user.home_folder_id
    search_query = "New Dataset in a folder"
    r = get_data_from_flask_jsonify(
        endpoint.search_within_folder(home_folder_id, search_query)
    )
    assert r["current_folder"]["id"] == home_folder_id
    assert len(r["entries"]) == 1
    assert r["entries"][0]["entry"]["id"] == new_dataset_in_new_folder_in_home.id


# <editor-fold desc="User">
# </editor-fold>


def test_setup_1(session: SessionBase):
    print("1")


def test_setup_2(session: SessionBase):
    print("2")
