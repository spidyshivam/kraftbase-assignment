from pydantic import BaseModel
from typing import Optional

class UserInDB(BaseModel):
    id: int
    username: str
    email: str
