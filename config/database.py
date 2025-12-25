from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 请确保这里的数据库连接信息是正确的
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:123123@localhost:3306/violation_management"

# 1. 创建引擎 (Engine)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 2. 创建会话工厂 (SessionLocal)
# 关键点：这里必须是 sessionmaker，而不是 engine.connect()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. 创建基类 (Base)
Base = declarative_base()

# 4. 获取数据库会话的依赖函数 (Dependency)
def get_db():
    # 关键点：实例化一个 Session 对象，而不是 Connection
    db = SessionLocal() 
    try:
        yield db
    finally:
        db.close()