Excellent Alex 👌 — this is proper architecture thinking.

You want:

* A **high-level database abstraction**
* Config-driven initialization (dictionary-based)
* Switchable backend:

  * MongoDB (using our `MongoService`)
  * Local JSON file storage
* Same interface regardless of backend
* Clean integration

That’s essentially building a **pluggable storage adapter pattern**.

We’ll implement:

```
Database (facade)
 ├── MongoAdapter
 └── JsonFileAdapter
```

Using:

* **PyMongo**
* **MongoDB**

---

# 🧠 Architecture Design

We define:

1. `BaseStorageAdapter` (interface)
2. `MongoAdapter` (wraps MongoService)
3. `JsonFileAdapter` (local storage)
4. `Database` (high-level entry point)

---

# 🔥 Implementation

---

## 1️⃣ Base Adapter Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseStorageAdapter(ABC):

    @abstractmethod
    def insert_one(self, collection: str, document: Dict) -> str:
        pass

    @abstractmethod
    def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        pass

    @abstractmethod
    def find(self, collection: str, query: Dict) -> List[Dict]:
        pass

    @abstractmethod
    def update_one(self, collection: str, query: Dict, update: Dict):
        pass

    @abstractmethod
    def delete_one(self, collection: str, query: Dict):
        pass

    @abstractmethod
    def close(self):
        pass
```

---

## 2️⃣ Mongo Adapter (Integration with MongoService)

```python
from typing import Dict, List, Optional
from bson import ObjectId


class MongoAdapter(BaseStorageAdapter):

    def __init__(self, config: Dict):
        from mongo_service import MongoService  # your previous wrapper

        self.mongo = MongoService(
            uri=config["uri"],
            db_name=config["db_name"]
        )

    def insert_one(self, collection: str, document: Dict) -> str:
        return self.mongo.insert_one(collection, document)

    def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        return self.mongo.find_one(collection, query)

    def find(self, collection: str, query: Dict) -> List[Dict]:
        return self.mongo.find(collection, query)

    def update_one(self, collection: str, query: Dict, update: Dict):
        return self.mongo.update_one(collection, query, update)

    def delete_one(self, collection: str, query: Dict):
        return self.mongo.delete_one(collection, query)

    def close(self):
        self.mongo.close()
```

---

## 3️⃣ JSON File Adapter (Local Storage)

Each collection = one JSON file.

```python
import os
import json
import uuid
from typing import Dict, List, Optional


class JsonFileAdapter(BaseStorageAdapter):

    def __init__(self, config: Dict):
        self.base_path = config.get("base_path", "./data")
        os.makedirs(self.base_path, exist_ok=True)

    def _file_path(self, collection: str) -> str:
        return os.path.join(self.base_path, f"{collection}.json")

    def _read_collection(self, collection: str) -> List[Dict]:
        path = self._file_path(collection)
        if not os.path.exists(path):
            return []

        with open(path, "r") as f:
            return json.load(f)

    def _write_collection(self, collection: str, data: List[Dict]):
        with open(self._file_path(collection), "w") as f:
            json.dump(data, f, indent=2)

    def insert_one(self, collection: str, document: Dict) -> str:
        data = self._read_collection(collection)

        document["_id"] = str(uuid.uuid4())
        data.append(document)

        self._write_collection(collection, data)
        return document["_id"]

    def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        data = self._read_collection(collection)
        for doc in data:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def find(self, collection: str, query: Dict) -> List[Dict]:
        data = self._read_collection(collection)
        return [
            doc for doc in data
            if all(doc.get(k) == v for k, v in query.items())
        ]

    def update_one(self, collection: str, query: Dict, update: Dict):
        data = self._read_collection(collection)

        for doc in data:
            if all(doc.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    doc.update(update["$set"])
                break

        self._write_collection(collection, data)

    def delete_one(self, collection: str, query: Dict):
        data = self._read_collection(collection)

        new_data = [
            doc for doc in data
            if not all(doc.get(k) == v for k, v in query.items())
        ]

        self._write_collection(collection, new_data)

    def close(self):
        pass
```

---

## 4️⃣ High-Level Database Class

This is what your application uses.

```python
class Database:

    def __init__(self, config: Dict):
        backend = config.get("backend")

        if backend == "mongo":
            self.adapter = MongoAdapter(config)

        elif backend == "json":
            self.adapter = JsonFileAdapter(config)

        else:
            raise ValueError("Unsupported backend type")

    # Delegate methods

    def insert_one(self, collection: str, document: Dict) -> str:
        return self.adapter.insert_one(collection, document)

    def find_one(self, collection: str, query: Dict):
        return self.adapter.find_one(collection, query)

    def find(self, collection: str, query: Dict):
        return self.adapter.find(collection, query)

    def update_one(self, collection: str, query: Dict, update: Dict):
        return self.adapter.update_one(collection, query, update)

    def delete_one(self, collection: str, query: Dict):
        return self.adapter.delete_one(collection, query)

    def close(self):
        self.adapter.close()
```

---

# 🚀 Example Usage

## Mongo Config

```python
config = {
    "backend": "mongo",
    "uri": "mongodb://localhost:27017",
    "db_name": "test_db"
}

db = Database(config)
```

---

## JSON Local Config

```python
config = {
    "backend": "json",
    "base_path": "./local_data"
}

db = Database(config)
```

---

# 🧠 Why This Design Is Senior-Level

You now have:

* Clean adapter pattern
* Backend swap without changing business logic
* Config-driven environment switching
* Test-friendly (use JSON backend for unit tests)
* Production-ready Mongo integration

---

# ⚠️ Important Notes

The JSON backend:

* ❌ Not thread-safe
* ❌ Not scalable
* ❌ No indexing
* ❌ No transactions

But:

* ✅ Perfect for local dev
* ✅ Perfect for testing
* ✅ No external dependency

---

If you want, next we can:

* 🔥 Add query operators support to JSON adapter ($gt, $in, etc.)
* ⚡ Add async version
* 🏗 Convert this to a repository-per-collection architecture
* 🧠 Integrate into your financial hash-chain storage model
* 🔐 Add file locking for thread safety

What level do you want to push this to?
