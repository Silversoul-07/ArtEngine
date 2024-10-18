from api.common import *
import api.routes.users.schemas as schemas
from api.routes.users.crud import create_dbuser, get_user_by_email, get_user_by_id, get_all_users, get_user_by_name, create_admin_user
from api.routes.users.utils import get_password_hash, verify_password, generate_name, random_avatar, get_token, get_db

router = APIRouter(prefix='/api', tags=['Users'])
oauth_schema = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
SECRET_KEY = os.getenv("SECRET_KEY")



@router.get("/users", response_model=List[schemas.User])
async def get_users(db: Session = Depends(get_db)):
    try:
        users = await get_all_users(db)
        return users
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/users", status_code=201)
async def create_user(db: Session = Depends(get_db),
    name: str = Form(...), 
    email: str = Form(...),
    password: str = Form(...)
    ):
    try:
        existing_user = await get_user_by_email(db, email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed_password = await get_password_hash(password)
        avatar = await random_avatar()
        kwargs = {
            "name": name,
            "email": email,
            "password": hashed_password,
            "avatar": avatar
        }
        created_user = await create_dbuser(db, **kwargs)
        return {"message": "User created", "user_id": created_user.id}
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.get("/users/{name}", response_model=schemas.UserDetail)
async def get_user(name: str, db: Session = Depends(get_db)):
    try:
        user = await get_user_by_name(db, name)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        logging.error(f"Error fetching user by name: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/session", response_model=schemas.Session)
async def get_user(request: Request, db: Session = Depends(get_db)):
    try:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="Token not found in cookies")

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logging.error(f"Error fetching user by id: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/auth", status_code=200)
async def auth_user(response: Response, form_data: schemas.UserValidate, db: Session = Depends(get_db)):
    try:
        user = await get_user_by_email(db, form_data.email)
        if not user or not await verify_password(form_data.password, user.password):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
    
        token = await get_token(
            data={"user_id": user.id}, 
            key=SECRET_KEY, 
            expires=datetime.timedelta(days=30)
        )
        
        response.set_cookie(key="token", value=token, httponly=True, max_age=30*24*60*60)
        
        session = {
            "name": user.name,
            "email": user.email,
            "avatar": user.avatar
        }
        session = jsonable_encoder(session)
        json_string = json.dumps(session)
        encoded_data = base64.b64encode(json_string.encode()).decode()
        print(encoded_data[:10])
        response.set_cookie(
            key="session", 
            value=encoded_data, 
            max_age=30*24*60*60, 
            samesite="lax"
        )        
        return {"message": "Authentication successful"}
    except Exception as e:
        logging.error(f"Error authenticating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")