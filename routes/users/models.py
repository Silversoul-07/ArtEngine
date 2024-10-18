from api.common import *

class Users(Base):
    __tablename__ = "users"

    id = Column(String(255), primary_key=True, index=True)  
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True, unique=True)
    password = Column(String(255), nullable=False)
    avatar = Column(String(255))
    about = Column(Text, default="No about yet :)")
    followers = Column(Integer, default=0)
    following = Column(Integer, default=0)
    favoriteTags = Column(ARRAY(String), default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __init__(self, **kwargs):
        super(Users, self).__init__(**kwargs)
        self.id = uuid4().hex

class UserFollows(Base):
    __tablename__ = "user_follows"

    user_id = Column(String(255), ForeignKey('users.id'), nullable=False, primary_key=True)
    follower_id = Column(String(255), ForeignKey('users.id'), nullable=False)
