from ...common import *

class Tags(BaseModel):
    tid: int
    name: str

class Image(BaseModel):
    url: str
    title: str
    desc: str
    tags: List[str]
    hash: str
    span: int
    isNSFW: bool
    uid: int

    class Config:
        orm_mode = True
