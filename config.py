import os
from urllib.parse import quote_plus


class Collections:
    def __init__(self):
        self.users = "users"
        self.items = "items"
        self.histories = "histories"
        self.categories = "categories"


# Database configuration
# mongodb://localhost:27017/
username = os.environ.get("MONGODB_USERNAME")
password = os.environ.get("MONGODB_PASSWORD")
MONGODB_URI = os.environ.get("MONGODB_URI")

if not username or not password or not MONGODB_URI:
    MONGODB_URI = "mongodb://localhost:27017/"
else:
    MONGODB_URI = MONGODB_URI.replace("<username>", quote_plus(username)).replace(
        "<password>", quote_plus(password)
    )

DATABASE = "shopmi"
COLLECTIONS = Collections()

AWS_ENABLE = bool(os.environ.get("AWS_ENABLE", False))
AWS_BUCKET = os.environ.get("AWS_BUCKET", "shopmi-bucket")
