from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import get_db
from models import schemas
from services import case_service
from db import crud

# 创建路由实例
# prefix="/api/cases" 意味着下面所有接口的 URL 都会以 /api/cases 开头
# tags=["案件管理"] 会在 Swagger 文档中把这些接口归为一组
router = APIRouter(prefix="/api/cases", tags=["案件管理"])

# ==========================================
# 辅助接口：地理位置 (为了能创建案件，必须先创建位置)
# ==========================================

@router.post("/locations", response_model=schemas.LocationOut, summary="创建地理位置")
def create_location(
    location: schemas.LocationCreate, 
    db: Session = Depends(get_db)
):
    """
    创建一个新的地理位置。
    返回的 ID 将用于后续创建案件时的 geolocation_id。
    """
    return crud.create_location(db=db, location=location)

# ==========================================
# 核心接口：案件管理 (CRUD + 业务逻辑)
# ==========================================

@router.post("/", response_model=schemas.CaseOut, status_code=status.HTTP_201_CREATED, summary="立案 (创建新案件)")
def create_new_case(
    case: schemas.CaseCreate, 
    db: Session = Depends(get_db)
):
    """
    创建新案件。
    - **逻辑**: 会自动生成 '2025xxxx' 格式的业务编号。
    - **校验**: 会检查占地面积是否大于建筑面积。
    """
    # 直接调用 Service 层，而不是 CRUD 层，因为我们需要 Service 处理编号生成逻辑
    return case_service.create_case(db=db, case_data=case)

@router.get("/", response_model=List[schemas.CaseOut], summary="获取案件列表")
def read_cases(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    分页获取案件列表。
    """
    # 读取列表这种简单操作，可以直接调用 CRUD，也可以通过 Service 转发
    return crud.get_cases(db, skip=skip, limit=limit)

@router.get("/{case_id}", response_model=schemas.CaseOut, summary="获取案件详情 (含全景时间轴)")
def read_case_detail(
    case_id: int, 
    db: Session = Depends(get_db)
):
    """
    根据 ID 获取案件详情。
    - 返回结果包含 **地理位置**。
    - 返回结果包含 **双视角进度列表** (enforcement_actions, violation_actions)。
    """
    return case_service.get_case_detail(db=db, case_id=case_id)

# ==========================================
# 业务接口：进度更新 (双视角)
# ==========================================

@router.post("/enforcement", response_model=schemas.DemolitionOut, summary="【执法视角】添加执法记录")
def add_enforcement_record(
    action: schemas.DemolitionCreate, 
    db: Session = Depends(get_db)
):
    """
    添加一条执法记录（如：发责令停止通知书）。
    - **自动化**: 会自动将关联案件的主状态 (status) 更新为当前动作的状态。
    """
    return case_service.add_enforcement_action(db=db, action_data=action)

@router.post("/violation-progress", response_model=schemas.ViolationProgressOut, summary="【业主视角】添加违建进度")
def add_violation_record(
    action: schemas.ViolationProgressCreate, 
    db: Session = Depends(get_db)
):
    """
    添加一条违建状态记录（如：业主仍在抢建）。
    - **自动化**: 会自动更新案件主状态。
    """
    return case_service.add_violation_action(db=db, action_data=action)

# ==========================================
# 结案接口
# ==========================================

@router.post("/conclusions", response_model=schemas.ConclusionOut, summary="案件结案归档")
def create_case_conclusion(
    conclusion: schemas.ConclusionCreate,
    db: Session = Depends(get_db)
):
    return crud.create_conclusion(db=db, conclusion=conclusion)