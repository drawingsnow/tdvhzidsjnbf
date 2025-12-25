import uvicorn
from fastapi import FastAPI
from config.database import engine, Base

# 导入模型以确保 SQLAlchemy 能够识别并创建表
# 这一步非常重要，否则 Base.metadata.create_all 无法扫描到表结构
from models import sqlalchemy_model  # noqa: F401

# 从 api 包中导入 cases 模块
# 注意：确保你的 api/cases.py 中已经定义了 case_router 和 location_router
from api import cases 

# 1. 【核心步骤】自动在数据库创建表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Case Management API", 
    version="0.1.0",
    description="违建案件管理系统 API"
)

# 2. 注册路由 (已更新)
# 我们现在有两个独立的路由器，需要分别注册

# 注册案件管理路由 (对应 /api/cases)
app.include_router(cases.case_router) 

# 注册地理位置路由 (对应 /api/locations)
app.include_router(cases.location_router)

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    # 建议 host 写 127.0.0.1 避免某些系统 localhost 解析慢的问题
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)