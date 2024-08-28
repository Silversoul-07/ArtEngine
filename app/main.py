import os
from dotenv import load_dotenv
import logging
import sys

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

load_dotenv()

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s:     %(message)s')
logger = logging.getLogger(__name__)

class DriveNotMounted(Exception):
    def __init__(self, message="Drive not mounted"):
        self.message = message
        super().__init__(self.message)

# ---------------------------------------------------------------------------------------------

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from app.routes.users.route import router as users_router
from app.routes.images.route import router as images_router
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.include_router(router=users_router)
app.include_router(router=images_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
STORAGE_DIR = os.getenv('STORAGE_DIR')
if not os.path.exists(STORAGE_DIR):
    raise DriveNotMounted()

app.mount("/media", StaticFiles(directory=STORAGE_DIR), name="public")

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="app/templates")

@app.get("/status")

@app.exception_handler(404)
async def custom_404_handler(request, __):
    return templates.TemplateResponse("404.html", {"request": request})