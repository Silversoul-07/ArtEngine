from ...common import *
from .models import Users, UserFollows

async def create_dbuser(db: Session, username, password, about, avatar, favourite_tags) -> None:
    db_user = Users(
        username=username, 
        password=password, 
        about=about, 
        avatar=avatar, 
        favourite_tags=favourite_tags
    )
    db.add(db_user)
    db.commit()

async def get_all_users(db: Session) -> List[Users]:
    return db.query(Users).all()

async def get_user_by_id(db: Session, uid: str) -> Users:
    return db.query(Users).filter(Users.uid == uid).first()

async def get_user_by_name(db: Session, username: str) -> Users:
    return db.query(Users).filter(Users.username == username).first()

async def add_follow(db: Session, uid: str, fid: str) -> None:
    db_follow = UserFollows(uid=uid, fid=fid)
    db.add(db_follow)
    db.commit()

async def get_follows_for_uid(db: Session, uid: str) -> Dict[str, List[str]]:
    user = await get_user_by_id(db, uid)
    if user is None:
        raise Exception("User not found")
    followers = [follower.uid for follower in user.followers]
    following = [followed.fid for followed in user.following]
    return {"followers": followers, "following": following}