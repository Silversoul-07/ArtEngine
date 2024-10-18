from api.common import *

class Media(Base):
    __tablename__ = "media"
    
    id = Column(BigInteger, primary_key=True, index=True)
    url = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    desc = Column(Text)
    hash = Column(String(64), unique=True, nullable=False)
    is_nsfw = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
    metadata_ = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    tags = relationship("Tag", secondary="media_tags", back_populates="media")
    collections = relationship("UserCollection", secondary="collection_media", back_populates="media")

    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_is_public', 'is_public'),
    )

    def __init__(self, **kwargs):
        super(Media, self).__init__(**kwargs)
        self.id = uuid4().time // 10000

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    
    media = relationship("Media", secondary="media_tags", back_populates="tags")

class MediaTags(Base):
    __tablename__ = "media_tags"
    
    media_id = Column(BigInteger, ForeignKey('media.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)

class UserCollection(Base):
    __tablename__ = "user_collections"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    media = relationship("Media", secondary="collection_media", back_populates="collections")

class CollectionMedia(Base):
    __tablename__ = "collection_media"
    
    collection_id = Column(Integer, ForeignKey('user_collections.id'), primary_key=True)
    media_id = Column(BigInteger, ForeignKey('media.id'), primary_key=True)

    
class UserPreferences(Base):
    """
    Table to store user preferences for media files.
    """
    __tablename__ = "user_preferences"
    
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False, primary_key=True)
    media_id = Column(BigInteger, ForeignKey('media.id'), nullable=False)
    preference = Column(Enum('like', 'dislike', name='preference_enum'), nullable=False)  # Enum to store user preference

class UserViewedMedia(Base):
    """
    Table to store records of media files viewed by users.
    """
    __tablename__ = "user_viewed_media"
    
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False, primary_key=True)
    media_id = Column(BigInteger, ForeignKey('media.id'), nullable=False)
    viewed_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    
    __table_args__ = (
        UniqueConstraint('user_id', 'media_id', name='unique_user_media_view'),  # Ensures no duplicate views
    )

# class UserRecommendedMedia(Base):
#     """
#     Table to store recommended media files for users.
#     """

#     __tablename__ = "user_recommended_media"
    
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
#     media_id = Column(BigInteger, ForeignKey('media.id'), nullable=False)
#     score = Column(Float, nullable=False)
#     created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

