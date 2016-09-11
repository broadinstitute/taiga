import persist
from tinydb import Query

home = [
    dict(name="origin"),
    dict(name="Folder A", children=[
        dict(name="Folder B", children=[
            dict(name="Data")
            ])
        ]),
        dict(name="A1 Data"),
        dict(name="A2 Data"),
        dict(name="A3 Data")
    ]

def add_entry(db, user_id, parent_id, proto, prov_dataset_ids):
    print("prov", prov_dataset_ids)
    if 'children' in proto:
        folder_id = db.add_folder(user_id, proto['name'], 'folder', proto.get("description", ""))
        assert db.add_folder_entry(parent_id, folder_id, 'folder')
        prev_dataset_version_ids = list(prov_dataset_ids)
        for c in proto['children']:
            prev_dataset_version_ids.extend(add_entry(db, user_id, folder_id, c, prev_dataset_version_ids))
        print("prev_dataset_version_ids", prev_dataset_version_ids)
        return prev_dataset_version_ids
    else:
        datafile_id = persist.new_id()
        db.register_datafile_id(datafile_id, datafile_id)
        entries = [persist.DatasetFile("data", "data description", "raw", datafile_id)]
        dataset_version_id = db.create_dataset(user_id, proto['name'], proto.get("description", ""), entries)
        db.update_datafile_summaries(dataset_version_id, "data", "10 x 13 table")
        db.add_folder_entry(parent_id, dataset_version_id, 'dataset_version')
        if len(prov_dataset_ids) > 0:
            print("adding prov")
            provenance = {
                'method': { 
                    'description': "Sample",
                    'parameters': {}
                },
                'inputs': [
                    {
                        'dataset_version_id' : dv_id, 
                        'name': 'data',
                        'method_parameter': 'input'
                    }
                    for dv_id in prov_dataset_ids
                ]
            }
            db.update_dataset_version_provenance(dataset_version_id, provenance)
        return [dataset_version_id]

# interface Method {
#     description: string;
#     parameters: string;
# }

# interface ProvSource {
#     dataset_version_id : string;
#     name : string;
#     method_parameter : string;
# }

# export interface Provenance {
#     method: Method;
#     inputs: Array<ProvSource>;
# }


if __name__ == "__main__":
    filename = "test.json"
    db = persist.open_db(filename)
    user_id = persist.setup_user(db, "admin")
    
    db.users.update(dict(id="admin"), Query()['id'] == user_id)
    user_id = 'admin'
    user = db.get_user(user_id)
    home_folder_id = user['home_folder_id']

    p = []
    for c in home:
       p.extend(add_entry(db, user_id, home_folder_id, c, p))
