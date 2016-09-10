import persist
from tinydb import Query

home = [
    dict(name="Folder A", children=[
        dict(name="Folder B", children=[
            dict(name="Data")
            ])
        ]),
        dict(name="A1 Data"),
        dict(name="A2 Data"),
        dict(name="A3 Data")
    ]

def add_entry(db, user_id, parent_id, proto):
    if 'children' in proto:
        folder_id = db.add_folder(user_id, proto['name'], 'folder', proto.get("description", ""))
        assert db.add_folder_entry(parent_id, folder_id, 'folder')
        for c in proto['children']:
            add_entry(db, user_id, folder_id, c)
    else:
        datafile_id = persist.new_id()
        db.register_datafile_id(datafile_id, datafile_id)
        entries = [persist.DatasetFile("data", "data description", "raw", datafile_id)]
        dataset_version_id = db.create_dataset(user_id, proto['name'], proto.get("description", ""), entries)
        db.update_datafile_summaries(dataset_version_id, "data", "10 x 13 table")
        db.add_folder_entry(parent_id, dataset_version_id, 'dataset_version')

if __name__ == "__main__":
    filename = "test.json"
    db = persist.open_db(filename)
    user_id = persist.setup_user(db, "admin")
    
    db.users.update(dict(id="admin"), Query()['id'] == user_id)
    user_id = 'admin'
    user = db.get_user(user_id)
    home_folder_id = user['home_folder_id']

    for c in home:
       add_entry(db, user_id, home_folder_id, c)
