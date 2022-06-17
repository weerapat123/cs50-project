import os

class Collections:
    def __init__(self):
        self.users = "users"
        self.items = "items"
        self.histories="histories"

# Database configuration
if not os.environ.get("MONGODB_URI"):
    MONGODB_URI = "mongodb://localhost:27017/"
else:
    MONGODB_URI = os.environ.get("MONGODB_URI")

DATABASE = "monkey_market"
COLLECTIONS = Collections()