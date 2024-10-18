from api.common import *
from api.routes.users.models import Users

# Function to create the admin user if it doesn't exist
async def create_admin_user(db: Session):
    if not db:
        raise Exception("Database connection error")
    # Path to the admin user data file
    admin_user_file = os.path.join('api/public', 'credentials.json')

    # Read the admin user data from the file
    with open(admin_user_file, 'r') as file:
        admin_user_data = json.load(file)

    # Check if the admin user already exists in the database
    existing_user = db.query(Users).filter_by(email=admin_user_data['email']).first()
    if not existing_user:
        # Create the admin user
        user = await create_dbuser(db, **admin_user_data)
        admin_user_data['id'] = user.id
        with open(admin_user_file, 'w') as file:
            json.dump(admin_user_data, file)

async def create_dbuser(db: Session, **kwargs):
    try:
        db_user = Users(**kwargs)
        db.add(db_user)
        db.commit()
        return db_user
    except Exception as e:
        db.rollback()
        raise e

async def get_user_by_email(db: Session, email: str):
    try:
        return db.query(Users).filter(Users.email == email).first()
    except Exception as e:
        logger.error(f"Error fetching user by email: {email}")
        raise

async def get_user_by_id(db: Session, id: str):
    try:
        return db.query(Users).filter(Users.id == id).first()
    except Exception as e:
        logger.error(f"Error fetching user by id: {id}")
        raise

async def get_all_users(db: Session):
    try:
        return db.query(Users).all()
    except Exception as e:
        logger.error(f"Error fetching all users: {e}")
        raise

async def get_user_by_name(db: Session, name: str):
    try:
        return db.query(Users).filter(Users.name == name).first()
    except Exception as e:
        logger.error(f"Error fetching user by name: {name}")
        raise