from sqlalchemy.orm import Session
from app.routes.users.models import Users

def create_user(db: Session,name:str,email:str,password:str,image:str):
    db_user = Users(
        name=name,
        email=email,
        password=password,
        image=image
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

def delete_user(db: Session, id: str):
    db.query(Users).filter(Users.id == id).delete()
    db.commit()

def get_user_by_email(db: Session, email:str):
    return db.query(Users).filter(Users.email == email).first()

def get_user_by_id(db: Session, id: str):
    return db.query(Users).filter(Users.id == id).first()
