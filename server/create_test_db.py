import persist
from tinydb import Query

if __name__ == "__main__":
    filename = "test.json"
    db = persist.open_db(filename)
    user_id = persist.setup_user(db, "admin")
    
    db.users.update(dict(id="admin"), Query()['id'] == user_id)
