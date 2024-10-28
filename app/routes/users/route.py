from ...common import *
from . import schemas
from .crud import create_dbuser, get_user_by_id, get_all_users, get_user_by_name, add_follow, get_follows_for_uid
from .utils import encrypt_password, verify_password, generate_names, save_avatar, get_token, get_db, validate_name

router = APIRouter(prefix='/api', tags=['Users'])

@router.get("/check_available", response_model=dict)
async def check_username(username: str, db: Session = Depends(get_db)):
    try:
        if not await validate_name(username):
            return {"available": False}
        user = await get_user_by_name(db, username)
        return {"available": user is None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/generate_name", response_model=dict)
async def generate_username():
    try:
        usernames = await generate_names()
        return {"username": usernames}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users", response_model=List[schemas.User])
async def get_users(db: Session = Depends(get_db)):
    try:
        users = await get_all_users(db)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users", status_code=201)
async def create_user(db: Session = Depends(get_db),
    username: str = Form(...), 
    password: str = Form(...),
    about: str = Form(...),
    avatar_image: UploadFile = File(...),
    tags = Form(...)
    ):
    try:
        if await get_user_by_name(db, username):
            raise Exception("User already exists")
        await validate_name(username)
        password = await encrypt_password(password)
        avatar = await save_avatar(avatar_image)
        favourite_tags = tags.split(",")
        await create_dbuser(db, username, password, about, avatar, favourite_tags)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/users/{username}", response_model=schemas.User)
async def get_user(username: str, db: Session = Depends(get_db)):
    try:
        user = await get_user_by_name(db, username)
        if not user:
            raise Exception("User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session", response_model=schemas.User)
async def get_session(uid: str = Depends(validate_user), db: Session = Depends(get_db)):
    try:
        print(uid)
        user = await get_user_by_id(db, uid)
        if not user:
            raise Exception("User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth", response_model=schemas.token)
async def auth_user(
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    try:
        user = await get_user_by_name(db, username)
        print(password, type(password))
        if not user:
            raise Exception("User not found")
        if not await verify_password(password, user.password):
            raise Exception("Invalid password")
        token = await get_token(
            data={"uid": str(user.uid)}, 
            expires=datetime.timedelta(days=30)
        )        
        return {"token": token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/follows", status_code=201)
async def follow_user(
    fid: str = Form(...),
    uid: str = Depends(validate_user),
    db: Session = Depends(get_db),
):
    try:
        await add_follow(db, uid, fid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/follows", response_model=schemas.Follows)
async def get_follows(count:bool = False, uid: str = Form(...),  db: Session = Depends(get_db)):
    try:
        result = await get_follows_for_uid(db, uid)
        print(count)
        if count:
            new_result = {}
            for key, value in result.items():
                new_result[key] = len(value)
            return new_result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))