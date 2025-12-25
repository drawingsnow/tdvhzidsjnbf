import uvicorn
from fastapi import FastAPI
from config.database import engine, Base
# 导入模型以确保 SQLAlchemy 能够识别并创建表
from models import sqlalchemy_model  # noqa: F401
# 假设你的文件路径是 api/cases.py，如果你的文件夹确实是 api/v1/cases.py，请保留你原来的导入方式
from api import cases 

# 1. 【核心步骤】自动在数据库创建表
# 程序启动时，SQLAlchemy 会去检查 models 定义，如果表不存在，就自动建表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Case Management API", 
    version="0.1.0",
    description="违建案件管理系统 API"
)

# 2. 注册路由
# 注意：cases.router 里面已经定义了 prefix="/api/cases"
# 所以这里我们直接 include，不需要再加 /api/v1，除非你想要 /api/v1/api/cases 这种结构
app.include_router(cases.router) 

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    # 建议 host 写 127.0.0.1 避免某些系统 localhost 解析慢的问题
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)