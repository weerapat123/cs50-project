import os
from urllib.parse import quote_plus


class Collections:
    def __init__(self):
        self.users = "users"
        self.items = "items"
        self.histories = "histories"


# Database configuration
# mongodb://localhost:27017/
username = os.environ.get("MONGODB_USERNAME")
password = os.environ.get("MONGODB_PASSWORD")

MONGODB_URI = f"mongodb+srv://{quote_plus(username)}:{quote_plus(password)}@my-cluster.lkefc.mongodb.net/?retryWrites=true&w=majority"
DATABASE = "monkey_market"
COLLECTIONS = Collections()
