from msilib.schema import Class


class Item:
    def __init__(self, item: dict):
        self.id = item.get("id")
        self.name = item.get("name")
        self.price = item.get("price")
        self.description = item.get("description")
        self.image_name = item.get("image_name")
        self.category = item.get("category")
        self.owner_id = item.get("owner_id")
        self.status = item.get("status")
