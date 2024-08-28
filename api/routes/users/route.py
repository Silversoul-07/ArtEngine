from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
import api.routes.users.schemas as schemas
from api.routes.users.crud import *
from api.routes.users.utils import *

router = APIRouter(prefix='/api', tags=['Users'])

@router.post("/users", status_code=201)
async def create_dbuser(user: schemas.UserCreate, db: Session = Depends(get_db)):
    isUser = await get_user_by_email(db, user.email)
    if isUser:
        raise HTTPException(status_code=400, detail="Email already registered")
    user.password = await get_password_hash(user.password)
    await create_user(db, 
                user.name,
                user.email,
                user.password,
                user.image)
    return {"message": "User created"}

@router.get("/users/{id}", response_model=schemas.User)
async def get_dbuser(id: int, db: Session = Depends(get_db)):
    user = await get_user_by_id(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user