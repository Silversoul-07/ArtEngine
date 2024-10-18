from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from api.database import Base, engine
from api.routes.users.route import router as users_router
from api.routes.images.route import router as images_router
from api.routes.users.crud import create_admin_user
from api.routes.users.utils import get_db
from api.routes.images.utils import sync_dir

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

app.mount("/avatar", StaticFiles(directory='media/avatar'), name="avatar")
app.mount("/images", StaticFiles(directory='media/images'), name="images")
app.mount("/gifs", StaticFiles(directory='media/gifs'), name="gifs")

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="api/templates")

@app.on_event("startup")
async def startup_event():
    async for db in get_db():
        await create_admin_user(db)
        await sync_dir(db, 'uploads/sync')

@app.get("/")
async def home():
    return RedirectResponse(url="/docs")

@app.exception_handler(404)
async def custom_404_handler(request, __):
    return templates.TemplateResponse("404.html", {"request": request})