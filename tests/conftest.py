# tests/conftest.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from typing import Generator

# 导入应用实例
from main import app
from config.database import get_db

# 【关键修正】：必须从定义模型的那个文件导入 Base
# 只有这个 Base.metadata 里才包含了 Geolocation 和 ViolationCase 的表结构
from models.sqlalchemy_model import Base

# 1. 配置测试数据库 (SQLite 内存版)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session() -> Generator:
    """
    数据库会话 Fixture
    """
    # 在内存数据库中创建所有表
    # 因为导入的是 models.sqlalchemy_model.Base，所以能正确找到表结构
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # 清理环境
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """
    TestClient Fixture
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()