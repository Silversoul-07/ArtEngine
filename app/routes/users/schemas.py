from ...common import *

class User(BaseModel):
    uid: str
    username: str
    about: str
    avatar: str
    favourite_tags: List[str]

    class Config:
        form_attributes = True

class token(BaseModel):
    token: str
    token_type: str

class Follows(BaseModel):
    followers: Union[int, List[str]]
    following: Union[int, List[str]]