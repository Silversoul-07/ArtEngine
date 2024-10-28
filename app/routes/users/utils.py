from ...common import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



async def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def encrypt_password(password) -> str:
    return pwd_context.hash(password)

async def generate_names(limit: int = 5) -> List[str]:
    arr = []
    for _ in range(limit):
        base_name = coolname.generate_slug(2).replace('-', '_')
        random_number = random.randint(10, 100)
        username = f"{base_name}{random_number}"
        arr.append(username)
    return arr

async def save_avatar(uploadImage: UploadFile) -> str:
    image = await uploadImage.read()
    format = Image.open(BytesIO(image)).format.lower()
    path = f"{STORAGE_DIR}/avatar/{uuid4().hex}.{format}"

    async with aiofile.async_open(path, "wb") as f:
        await f.write(image)
    return path

async def validate_name(name: str) -> bool:
    if not re.match("^[a-zA-Z0-9_]*$", name):
        return False
    return True

async def get_token(data: dict, expires: datetime.timedelta = None) -> str:
    to_encode = {"sub": data}
    if expires:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires
        to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm)
