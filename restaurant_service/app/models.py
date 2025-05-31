from tortoise import fields
from tortoise.models import Model

class Restaurant(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    online = fields.BooleanField(default=True)

class MenuItem(Model):
    id = fields.IntField(pk=True)
    restaurant = fields.ForeignKeyField('models.Restaurant', related_name='menu_items')
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    available = fields.BooleanField(default=True)

class Order(Model):
    id = fields.IntField(pk=True)
    restaurant = fields.ForeignKeyField('models.Restaurant', related_name='orders')
    user_id = fields.IntField()
    status = fields.CharField(max_length=50)
    items = fields.JSONField()
    assigned_agent_id = fields.IntField(null=True)
    restaurant_rating = fields.IntField(null=True)
    agent_rating = fields.IntField(null=True)
