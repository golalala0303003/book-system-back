from sqlmodel import create_engine, Session
from app.core.config import settings

# 在使用的地方进行动态组装
DATABASE_URL = (
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
)

# 创建全局的数据库引擎
engine = create_engine(DATABASE_URL, echo=True)

def get_db():
    """
    为每个请求创建一个独立的数据库会话 Session，并在请求结束后自动关闭。
    """
    with Session(engine) as session:
        yield session