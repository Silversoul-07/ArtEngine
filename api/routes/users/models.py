from sqlalchemy import Column, Integer, String
from api.database import Base

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255))
    email = Column(String(255), index=True)
    password = Column(String(255))
    image = Column(String(255))