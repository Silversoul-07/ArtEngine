from ...common import *

class Media(Base):
    __tablename__ = "media"
    
    mid = Column(String(255), primary_key=True, index=True)
    url = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    desc = Column(Text)
    hash = Column(String(255), unique=True)
    span = Column(Integer, default=0)
    src = Column(String(255))
    score = Column(Integer, default=0)
    color = Column(String(255), nullable=True)
    isNSFW = Column(Boolean, default=False)
    uid = Column(String(255), ForeignKey('users.uid', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    owner = relationship("Users", backref=backref("media", lazy="dynamic"))
    tags = relationship("Tags", secondary="media_tags", back_populates="media")
    collections = relationship("Collections", secondary="collection_media", back_populates="media")
    likes = relationship("Preferences", primaryjoin="and_(Preferences.mid==Media.mid, Preferences.attr=='like')")
    dislikes = relationship("Preferences", primaryjoin="and_(Preferences.mid==Media.mid, Preferences.attr=='dislike')")

    __table_args__ = (Index('idx_user_id', 'uid'),)

    def __init__(self, **kwargs):
        super(Media, self).__init__(**kwargs)
        self.mid = str(uuid4().int >> 64) 

class Tags(Base):
    __tablename__ = "tags"
    
    tid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)

    media = relationship("Media", secondary="media_tags", back_populates="tags")
    collections = relationship("Collections", secondary="collection_tags", back_populates="tags")

class MediaTags(Base):
    __tablename__ = "media_tags"
    
    mid = Column(String(255), ForeignKey('media.mid', ondelete='CASCADE'), primary_key=True)
    tid = Column(Integer, ForeignKey('tags.tid', ondelete='CASCADE'), primary_key=True)

class Collections(Base):
    __tablename__ = "collections"
    
    cid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    desc = Column(Text)
    scope = Column(Enum('public', 'private', name='scope_enum'), default='public')
    uid = Column(String(255), ForeignKey('users.uid', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    media = relationship("Media", secondary="collection_media", back_populates="collections")
    tags = relationship("Tags", secondary="collection_tags", back_populates="collections")
    access_list = relationship("Users", secondary="collection_access_list", back_populates="collections")
    owner = relationship("Users", back_populates="owned_collections")

class CollectionTags(Base):
    __tablename__ = "collection_tags"
    
    cid = Column(Integer, ForeignKey('collections.cid', ondelete='CASCADE'), primary_key=True)
    tid = Column(Integer, ForeignKey('tags.tid', ondelete='CASCADE'), primary_key=True)

class CollectionAccessList(Base):
    __tablename__ = "collection_access_list"
    
    cid = Column(Integer, ForeignKey('collections.cid', ondelete='CASCADE'), primary_key=True)
    uid = Column(String(255), ForeignKey('users.uid', ondelete='CASCADE'), primary_key=True)

class CollectionAccessRequest(Base):
    __tablename__ = "collection_access_request"
    
    cid = Column(Integer, ForeignKey('collections.cid', ondelete='CASCADE'), primary_key=True)
    uid = Column(String(255), ForeignKey('users.uid', ondelete='CASCADE'), primary_key=True)
    requested_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint('cid', 'uid', name='unique_user_collection_request'),)

class CollectionFollowers(Base):
    __tablename__ = "collection_followers"
    
    cid = Column(Integer, ForeignKey('collections.cid', ondelete='CASCADE'), primary_key=True)
    uid = Column(String(255), ForeignKey('users.uid', ondelete='CASCADE'), primary_key=True)

    __table_args__ = (UniqueConstraint('cid', 'uid', name='unique_user_collection_follow'),)

class CollectionMedia(Base):
    __tablename__ = "collection_media"
    
    cid = Column(Integer, ForeignKey('collections.cid', ondelete='CASCADE'), primary_key=True)
    mid = Column(String(255), ForeignKey('media.mid', ondelete='CASCADE'), primary_key=True)

    collection = relationship("Collections", backref=backref("collection_media", lazy="dynamic"))
    media = relationship("Media", backref=backref("collection_media", lazy="dynamic"))

class Preferences(Base):
    __tablename__ = "preferences"
    
    uid = Column(String(255), ForeignKey('users.uid', ondelete='CASCADE'), nullable=False, primary_key=True)
    mid = Column(String(255), ForeignKey('media.mid', ondelete='CASCADE'), nullable=False, primary_key=True)
    attr = Column(Enum('like', 'dislike', name='preference_enum'), nullable=False)

    __table_args__ = (Index('idx_uid_mid', 'uid', 'mid'),)

class Activity(Base):
    __tablename__ = "activity"
        
    uid = Column(String(255), ForeignKey('users.uid', ondelete='CASCADE'), nullable=False, primary_key=True)
    mid = Column(String(255), ForeignKey('media.mid', ondelete='CASCADE'), nullable=False, primary_key=True)
    viewed_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint('uid', 'mid', name='unique_user_media_view'),)
