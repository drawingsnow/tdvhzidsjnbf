from config.database import engine, Base
from models import sqlalchemy_model# 必须导入模型，否则找不到表

print("正在删除旧表...")
Base.metadata.drop_all(bind=engine) # 💥 删库（仅限当前定义的表）

print("正在创建新表...")
Base.metadata.create_all(bind=engine) # ✨ 重建

print("数据库重置完成！请重新运行 main.py")