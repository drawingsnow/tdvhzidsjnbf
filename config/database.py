import logging

import pymysql
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import declarative_base  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore

logger = logging.getLogger(__name__)

# 数据库配置（与现有 app.py 保持一致，按需修改）
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123123",  # 请替换为真实密码
    "database": "violation_management",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

# SQLAlchemy 配置
# 构建数据库连接字符串: mysql+pymysql://user:password@host/database
DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"

# 创建 SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# 创建 SessionLocal 类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建 Base 类，用于定义模型
Base = declarative_base()


def get_db_connection():
    """创建并返回一个新的数据库连接。"""
    return pymysql.connect(**DB_CONFIG)


def get_db():
    """
    FastAPI 依赖：提供数据库连接，自动提交/回滚并关闭。
    在路由层通过 Depends(get_db) 使用。
    """
    conn = None
    try:
        conn = get_db_connection()
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

