import requests

def wait_for_import(import_status):
    dataset_version_id = import_status['id']
    while import_status['status'] in ['pending', 'running']:
        print (import_status['message'])
        import_status = get("datasetVersion/"+dataset_version_id+"/status")
    assert import_status['status'] == 'complete'
    return dataset_version_id

# get current user
user = get("user")
home_folder_id = user['home_folder_id']

# create a folder under home folder
child_folder = post("folders/create", dict(name="child", description="folder description", parent=home_folder_id))
child_folder_id = child_folder['id']
home_contents = get("folder/"+home_folder_id)
child = get("folder/"+child_folder_id)

# create a dataset consisting of a single uploaded file
upload = get("uploadurl")
post(upload['url'], raw="abc")
import_status = post("datasets/create", dict(name="dataset", description="dataset description", parent=child_folder_id, entries=[
    dict(name="datafile", type="raw", description="datafile description", id=upload['id'])
    ]
    ))
dataset_version_id = wait_for_import(import_status)
dataset_version = get("datasetVersion/"+dataset_version_id)
dataset_id = dataset_version['dataset_id']

child_contents = get("folder/"+child_folder_id)

# create a new version of the dataset with a new file
upload2 = get("uploadurl")
post(upload2['url'], raw="abcdefg")
import_status = post("dataset/"+dataset_id+"/update", dict(new_entries=[
    dict(name="datafile", type="raw", description="datafile description", id=upload['id'])
    ]
    ))
wait_for_import(import_status)

# remove dataset
post("folders/update", dict(operations=[
    dict(parent=child_folder_id,
        opType="remove",
        idType="dataset",
        id=dataset_id)]))

# remove folder
post("folders/update", dict(operations=[
    dict(parent=home_folder_id,
        opType="remove",
        idType="folder",
        id=child_folder_id)]))


