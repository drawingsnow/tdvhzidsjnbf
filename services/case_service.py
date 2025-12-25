from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException

from db import crud
from models import schemas
from models.sqlalchemy_model import ViolationCase  # type: ignore

# ============================================
# 核心逻辑 1: 智能案件编号生成器
# ============================================
def generate_case_number(db: Session) -> str:
    """
    生成业务编号，规则：当前年份 + 4位自增序号 (例如: 20250001)
    逻辑：
    1. 获取当前年份 (2025)
    2. 查询数据库中，今年最大的那个编号是多少
    3. 如果没有，就从 20250001 开始
    4. 如果有 (例如 20250005)，就加 1 变成 20250006
    """
    current_year = str(datetime.now().year)
    
    # 在数据库中查找以当前年份开头，且编号最大的那个案件
    # 这里的 filter 相当于 SQL: WHERE case_number LIKE '2025%'
    last_case = (
        db.query(ViolationCase)
        .filter(ViolationCase.case_number.like(f"{current_year}%"))
        .order_by(ViolationCase.case_number.desc())
        .first()
    )

    if not last_case:
        # 如果今年还没案件，从 0001 开始
        return f"{current_year}0001"
    
    # 解析旧编号：拿出后4位 (例如 "20250012" -> "0012")
    last_seq_str = last_case.case_number[4:] 
    
    # 转成数字加 1
    new_seq = int(last_seq_str) + 1
    
    # 格式化回字符串，不足4位补零 (例如 13 -> "0013")
    return f"{current_year}{new_seq:04d}"

# ============================================
# 核心业务: 创建案件
# ============================================
def create_case(db: Session, case_data: schemas.CaseCreate):
    """
    创建案件的标准流程：
    1. 校验数据 (面积逻辑)
    2. 生成编号
    3. 写入数据库
    """
    # 1. 业务校验：占地面积不能大于建筑面积 (如果这是你的业务规则)
    # 虽然 Schema 里可能有校验，但这里是最后一道防线
    if case_data.land_area > case_data.building_area:
         # 这里的 HTTPException 会直接被 FastAPI 捕获并返回 400 给前端
        raise HTTPException(status_code=400, detail="数据逻辑错误：占地面积不能大于建筑面积")

    # 2. 生成唯一的业务编号
    new_number = generate_case_number(db)

    # 3. 调用 CRUD 入库
    return crud.create_violation_case(db=db, case=case_data, case_number=new_number)

# ============================================
# 核心业务: 获取详情 (包含双视角)
# ============================================
def get_case_detail(db: Session, case_id: int):
    case = crud.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="未找到该案件")
    return case

# ============================================
# 核心逻辑 2: 状态联动 (双视角驱动主状态)
# ============================================

def add_enforcement_action(db: Session, action_data: schemas.DemolitionCreate):
    """
    【执法者视角】添加记录 -> 自动更新主表状态
    例如：添加了一条“强制拆除”的记录，主表状态也应该变为“强制拆除”
    """
    # 1. 检查案件是否存在
    case = crud.get_case(db, action_data.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="关联的案件不存在")

    # 2. 创建执法记录
    new_record = crud.create_enforcement_action(db, action_data)

    # 3. 【联动逻辑】将案件主表的状态，更新为这条最新记录的状态
    # 这样在列表页，我们就能看到这个案件目前的最新进展
    crud.update_case_status(db, case_id=action_data.case_id, new_status=action_data.status)

    return new_record

def add_violation_action(db: Session, action_data: schemas.ViolationProgressCreate):
    """
    【业主视角】添加记录 -> 自动更新主表状态
    例如：业主又开始“抢建”了，主表状态更新为“抢建中”
    """
    case = crud.get_case(db, action_data.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="关联的案件不存在")

    new_record = crud.create_violation_action(db, action_data)

    # 联动更新主状态
    crud.update_case_status(db, case_id=action_data.case_id, new_status=action_data.status)

    return new_record