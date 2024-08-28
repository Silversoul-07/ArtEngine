from passlib.context import CryptContext
from api.database import SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def get_password_hash(password):
    return pwd_context.hash(password)

