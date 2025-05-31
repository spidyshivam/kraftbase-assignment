from pydantic import BaseModel

class DeliveryAssignment(BaseModel):

    order_id: int

class DeliveryAgentIn(BaseModel):

    name: str
    available: bool = True

class DeliveryAgentOut(BaseModel):

    id: int
    name: str
    available: bool

    class Config:
        from_attributes = True

class DeliveryComplete(BaseModel):
    order_id: int
    agent_id: int

class DeliveryCompletionResponse(BaseModel):
    msg: str
    agent_id: int
    agent_available: bool
    order_status_updated: bool
