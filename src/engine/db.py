from datetime import datetime

try:
    import pymongo
except ModuleNotFoundError:
    pymongo = None

URL = "mongodb://@host:27017/?authSource=admin"
DB = "ATSDB"


class Db:
    def __init__(self, url=URL, db=DB):
        if pymongo is None:
            self.client = None
            self.connection = None
            return

        self.client = pymongo.MongoClient(serverSelectionTimeoutMS=5000)
        self.connection = self.client[db]

    def _collection(self, collection):
        if self.connection is None:
            raise RuntimeError("pymongo is required for database operations")
        return self.connection[collection]

    # def insert_one(self, collection, doc):
    #     res = self.connection[collection].insert_one(doc)
    #     return res.inserted_id

    def update_one(self, collection, query, update_doc, upsert=False):
        res = self._collection(collection).update_one(
            query, {"$set": update_doc}, upsert=upsert
        )

    def insert_one(self, collection, update_doc):
        res = self._collection(collection).insert_one(update_doc)
        return res

    def find_by_id(self, collection, _id):
        res = self.find_one(collection, {"_id": _id})  # [collection].find_one(query)
        return res

    def find_one(self, collection, query):
        res = self._collection(collection).find_one(query)
        return res


database = Db()
