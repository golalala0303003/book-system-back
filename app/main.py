from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api import user_controller
from app.api import upload_controller
from sqlmodel import SQLModel
from app.core.db import engine
from contextlib import asynccontextmanager
from app import models
from app.exceptions.handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("启动！Ciallo～ (∠・ω< )⌒★")
    SQLModel.metadata.create_all(engine)
    yield
    print("再见！")

app = FastAPI(title="Ciallo～ (∠・ω< )⌒★", lifespan=lifespan)
origins = [
    "http://localhost:5173",  # Vite 默认端口
    "http://localhost:8080",  # Webpack 默认端口
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # 允许的源列表
    allow_credentials=True,      # 允许前端携带凭证 (如 Cookie、Authorization 头)
    allow_methods=["*"],         # 允许所有的 HTTP 方法 (GET, POST, PUT, DELETE, OPTIONS等)
    allow_headers=["*"],         # 允许所有的请求头
)
app.include_router(user_controller.router)
app.include_router(upload_controller.router)
register_exception_handlers(app)

@app.get("/")
async def root():
    return {"message": "Hello World"}
