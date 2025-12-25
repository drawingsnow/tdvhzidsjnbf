from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import sqlalchemy_model as models
from models import schemas

# ============================================
# 1. 地理位置 (Location) - 基础数据
# ============================================

def get_location(db: Session, location_id: int):
    """根据 ID 查询地理位置"""
    return db.query(models.GeographicalLocation).filter(models.GeographicalLocation.id == location_id).first()

def create_location(db: Session, location: schemas.LocationCreate):
    """创建新的地理位置"""
    db_location = models.GeographicalLocation(**location.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

# ============================================
# 2. 案件管理 (Case) - 核心增删改查
# ============================================

def get_case(db: Session, case_id: int):
    """根据 ID 查询案件详情（包含关联的双视角进度）"""
    return db.query(models.ViolationCase).filter(models.ViolationCase.id == case_id).first()

def get_case_by_number(db: Session, case_number: str):
    """根据业务编号查询案件 (例如: 20250001)"""
    return db.query(models.ViolationCase).filter(models.ViolationCase.case_number == case_number).first()

def get_cases(db: Session, skip: int = 0, limit: int = 100):
    """查询案件列表（支持分页）"""
    return db.query(models.ViolationCase).offset(skip).limit(limit).all()

def create_violation_case(db: Session, case: schemas.CaseCreate, case_number: str):
    """
    创建案件
    注意：case_number 是由 Service 层生成后传进来的，不在 schemas.CaseCreate 里
    """
    # 1. 将 Pydantic schema 转换为字典
    case_data = case.model_dump()
    
    # 2. 实例化 SQLAlchemy 模型，并手动注入 case_number
    db_case = models.ViolationCase(**case_data, case_number=case_number)
    
    # 3. 存入数据库
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

def update_case_status(db: Session, case_id: int, new_status: str):
    """
    更新案件的主状态
    通常由 Service 层在添加进度记录后调用
    """
    db_case = get_case(db, case_id)
    if db_case:
        db_case.status = new_status
        db.commit()
        db.refresh(db_case)
    return db_case

# ============================================
# 3. 双视角进度管理 (Progress)
# ============================================

def create_enforcement_action(db: Session, action: schemas.DemolitionCreate):
    """
    【执法者视角】新增执法记录 (如：发通知书、强拆)
    """
    db_action = models.DemolitionProgress(**action.model_dump())
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action

def create_violation_action(db: Session, action: schemas.ViolationProgressCreate):
    """
    【业主视角】新增违建状态记录 (如：抢建、停工)
    """
    db_action = models.BuildingViolationProgress(**action.model_dump())
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action

# ============================================
# 4. 结案归档 (Conclusion)
# ============================================

def create_conclusion(db: Session, conclusion: schemas.ConclusionCreate):
    """创建结案记录"""
    db_conclusion = models.ConclusionStatistics(**conclusion.model_dump())
    db.add(db_conclusion)
    db.commit()
    db.refresh(db_conclusion)
    return db_conclusion