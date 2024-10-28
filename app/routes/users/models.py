from ...common import *

class Users(Base):
    __tablename__ = "users"

    uid = Column(String(255), primary_key=True, index=True)  
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    about = Column(Text, nullable=False)
    avatar = Column(String(255))
    favourite_tags = Column(ARRAY(String), default=[])
    is_private = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Bidirectional relationships for followers and following
    followers = relationship(
        "UserFollows",
        foreign_keys="UserFollows.fid",
        back_populates="following_user",
        cascade="all, delete-orphan"
    )
    following = relationship(
        "UserFollows",
        foreign_keys="UserFollows.uid",
        back_populates="follower_user",
        cascade="all, delete-orphan"
    )

    owned_collections = relationship("Collections", back_populates="owner")
    collections = relationship("Collections", secondary="collection_access_list", back_populates="access_list")

    def __init__(self, **kwargs):
        super(Users, self).__init__(**kwargs)
        self.uid = uuid4().hex[:20]  # Generating a 16-char hex UUID

class UserFollows(Base):
    __tablename__ = "user_follows"

    uid = Column(String(255), ForeignKey('users.uid', ondelete="CASCADE"), nullable=False, primary_key=True)  # Follower
    fid = Column(String(255), ForeignKey('users.uid', ondelete="CASCADE"), nullable=False, primary_key=True)  # Followed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Establishing relationships for bidirectional follow connections
    follower_user = relationship("Users", foreign_keys=[uid], back_populates="following")
    following_user = relationship("Users", foreign_keys=[fid], back_populates="followers")

    __table_args__ = (
        Index('idx_following_user', 'uid', 'fid'),  # Composite index for fast follower lookups
    )
    