from tortoise import fields
from tortoise.models import Model

class DeliveryAgent(Model):
    """
    Tortoise ORM model for a Delivery Agent.
    """
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    available = fields.BooleanField(default=True)

    class Meta:
        table = "delivery_agents" 
