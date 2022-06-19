import os
from urllib.parse import quote_plus


class Collections:
    def __init__(self):
        self.users = "users"
        self.items = "items"
        self.histories = "histories"


# Database configuration
# mongodb://localhost:27017/
username = os.environ.get("MONGODB_USERNAME", "")
password = os.environ.get("MONGODB_PASSWORD", "")

if not username or not password:
    MONGODB_URI = "mongodb://localhost:27017/"
else:
    MONGODB_URI = f"mongodb+srv://{quote_plus(username)}:{quote_plus(password)}@my-cluster.lkefc.mongodb.net/?retryWrites=true&w=majority"

DATABASE = "shopmi"
COLLECTIONS = Collections()

AWS_ENABLE = bool(os.environ.get("AWS_ENABLE", False))
AWS_BUCKET = os.environ.get("AWS_BUCKET", "shopmi-bucket")
