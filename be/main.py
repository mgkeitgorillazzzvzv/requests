from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from dotenv import load_dotenv
from routes.users import router as users_router
from routes.requests import router as requests_router
from routes.notifications import router as notifications_router
from routes.stats import router as stats_router
import os

load_dotenv()

app = FastAPI()

register_tortoise(
    app,
    db_url=os.getenv("DATABASE_URL", "sqlite://db.sqlite3"),
    modules={'models': ['models.tortoise']},
    generate_schemas=True,
    add_exception_handlers=True,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(requests_router, prefix="/requests", tags=["requests"])
app.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
app.include_router(stats_router, prefix="/stats", tags=["stats"])

@app.get("/version", tags=["system"])
async def get_version():
    """Get frontend version"""
    try:
        version_path = os.path.join(os.path.dirname(__file__), 'version.txt')
        with open(version_path, 'r') as f:
            version = f.read().strip()
        return {"version": version}
    except FileNotFoundError:
        return {"version": "1.0.0"}

@app.on_event("startup")
async def create_admin_user_on_startup():
    admin_user = os.getenv("ADMIN_USER")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_user or not admin_password:
        return

    
    from models.tortoise import User
    from models.enums import Role

    from auth import pwd_context
    hashed = pwd_context.hash(admin_password)

    existing = await User.get_or_none(username=admin_user)
    if existing:
        return

    await User.create(
        username=admin_user,
        password=hashed,
        first_name="Administrator",
        last_name=admin_user,
        role=Role.ADMIN,
    )
