from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from .database import Base, engine
from .routes.users.route import router as users_router
from .routes.images.route import router as images_router
import os
# from .routes.users.crud import create_admin_user
from .routes.users.utils import get_db
from .routes.images.crud import update_tags_from_list
from .routes.images.utils import sync_dir
import asyncio  
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    db = await anext(get_db())
    task = asyncio.create_task(update_tags_from_list(db), name="Update Tags")

    yield
    # Shutdown logic
    task.cancel()
    await task
    

app = FastAPI(lifespan=lifespan)
app.include_router(router=users_router)
app.include_router(router=images_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_DIR = os.getenv("STORAGE_DIR")
os.makedirs(f"{STORAGE_DIR}/avatar", exist_ok=True)
os.makedirs(f"{STORAGE_DIR}/images", exist_ok=True)
os.makedirs(f"{STORAGE_DIR}/clips", exist_ok=True)

app.mount("/avatar", StaticFiles(directory=f"{STORAGE_DIR}/avatar"), name="avatar")
app.mount("/images", StaticFiles(directory=f"{STORAGE_DIR}/images"), name="images")
app.mount("/gifs", StaticFiles(directory=f"{STORAGE_DIR}/clips"), name="clips")

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="app/templates")



@app.get("/")
async def home():
    return RedirectResponse(url="/docs")

@app.exception_handler(404)
async def custom_404_handler(request, __):
    return templates.TemplateResponse("404.html", {"request": request})