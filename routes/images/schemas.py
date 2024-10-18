from api.common import *

class Image(BaseModel):
    id: int
    url: str
    title: str
    desc: str
    tags: List[str]
    collections: List[str]
    is_nsfw: bool
    metadata_: Dict[str, Any]
    created_at: datetime.datetime

    class Config:
        form_attributes = True

class Images(BaseModel):
    root : List[Image]
