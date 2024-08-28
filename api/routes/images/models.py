from sqlalchemy import Column, Integer, String, BigInteger, Boolean
from api.database import Base
from pgvector.sqlalchemy import Vector
import os
import random
from uuid import uuid4

class Images(Base):
    __tablename__ = "images"

    id = Column(BigInteger, primary_key=True, index=True)
    url = Column(String(64))
    title = Column(String(255))
    hash = Column(String(64), unique=True)
    is_nsfw = Column(Boolean, default=False)
    user_id = Column(Integer)

    def __init__(self, url, title, hash, user_id):
        self.id = self.generate_random_id()
        self.url = self.get_url(url)
        self.title = title
        self.hash = hash
        self.user_id = user_id

    @staticmethod
    def generate_random_id():
        return random.randint(10**15, 10**16 - 1)

    @staticmethod
    def get_url(url):
        ext = os.path.splitext(url)[1]
        return f"{uuid4().time}{ext}"       
     
class Embeddings(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    embed = Column(Vector(768) )
    image_id = Column(BigInteger, index=True)
