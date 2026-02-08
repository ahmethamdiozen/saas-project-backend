from fastapi import FastAPI
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as user_router
from app.db import models

app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)
