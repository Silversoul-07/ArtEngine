from pydantic import BaseModel
from typing import List

class CreateImage(BaseModel):
    url: str
    title: str
    hash: str
    embed: List[float]
    user_id: int

    class Config:
        form_attributes = True

class Image(BaseModel):
    id: int
    url: str
    title: str

    class Config:
        form_attributes = True

class Images(BaseModel):
    root : List[Image]

