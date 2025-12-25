from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import get_db
from models import schemas
from services import case_service
from db import crud

# ==========================================
# 路由定义
# ==========================================

# 1. 案件管理路由 (前缀: /api/cases)
case_router = APIRouter(prefix="/api/cases", tags=["案件管理"])

# 2. 地理位置路由 (前缀: /api/locations)
# 为了满足需求中的 URL 结构，单独定义一个 router
# 注意：请确保在 main.py 中 include_router(api.cases.location_router)
location_router = APIRouter(prefix="/api/locations", tags=["地理位置"])


# ==========================================
# A. 地理位置相关接口 (Location Router)
# ==========================================

@location_router.post("/", response_model=schemas.GeolocationRead, status_code=status.HTTP_201_CREATED, summary="创建地理位置")
def create_location(
    location: schemas.GeolocationCreate, 
    db: Session = Depends(get_db)
):
    """
    创建一个新的地理位置。
    返回的 ID 将用于后续创建案件时的 geolocation_id。
    """
    return crud.create_location(db=db, location=location)

@location_router.get("/{location_id}/history", response_model=schemas.GeolocationRead, summary="获取位置历史案件")
def get_location_history(
    location_id: int,
    db: Session = Depends(get_db)
):
    """
    [新增需求] 获取该地理位置下关联的所有历史案件。
    - 利用 GeolocationRead 中的 `cases` 字段返回简要历史列表。
    - 按创建时间倒序排列 (需在 ORM relationship 中配置或前端处理，此处返回完整对象)
    """
    location = crud.get_location(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="未找到该地理位置")
    return location


# ==========================================
# B. 案件管理核心接口 (Case Router)
# ==========================================

@case_router.post("/", response_model=schemas.ViolationCaseList, status_code=status.HTTP_201_CREATED, summary="立案 (创建新案件)")
def create_new_case(
    case: schemas.ViolationCaseCreate, 
    db: Session = Depends(get_db)
):
    """
    创建新案件。
    - **逻辑**: 自动生成 '2025xxxx' 业务编号，支持位置智能复用。
    - **校验**: 检查占地面积 <= 建筑面积。
    """
    # 这里的 case_data 包含 geolocation_id
    # 如果需要支持同时传入位置信息，需修改入参结构，此处保持基础逻辑
    return case_service.create_case_service(db=db, case_in=case)

@case_router.get("/", response_model=List[schemas.ViolationCaseList], summary="获取案件列表")
def read_cases(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    分页获取案件列表 (仅返回简要信息，不含大量关联记录)。
    """
    return crud.get_cases(db, skip=skip, limit=limit)

@case_router.get("/{case_id}", response_model=schemas.ViolationCaseDetail, summary="获取案件详情 (全景视图)")
def read_case_detail(
    case_id: int, 
    db: Session = Depends(get_db)
):
    """
    根据 ID 获取案件详情。
    - **政府视角**: enforcement_actions
    - **业主视角**: building_progresses
    - **档案**: archives
    """
    case = case_service.get_case_detail(db=db, case_id=case_id) # 假设 service 层有此封装，或直接调 crud
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    return case

@case_router.get("/{case_id}/archive-check", summary="检查档案完整性")
def check_case_archive(
    case_id: int,
    db: Session = Depends(get_db)
):
    """
    [新增需求] 自动化档案检查
    - 根据案件当前的 status (执法阶段)，比对已上传文件。
    - 返回缺失的文件清单。
    """
    # 直接调用 Service 层的逻辑
    # 返回的是 dataclass，FastAPI 可以直接将其序列化为 JSON
    return case_service.check_archive_status(db=db, case_id=case_id)


# ==========================================
# C. 进度更新接口 (双视角)
# ==========================================

@case_router.post("/enforcement", response_model=schemas.EnforcementActionRead, summary="【执法视角】添加执法记录")
def add_enforcement_record(
    action: schemas.EnforcementActionCreate, 
    db: Session = Depends(get_db)
):
    """
    政府/执法队操作：添加执法记录（如：发责令停止通知书）。
    - **自动化**: 自动更新案件主状态 (status)。
    """
    return case_service.add_enforcement_action_service(db=db, action_data=action)

@case_router.post("/building-progress", response_model=schemas.BuildingProgressRead, summary="【业主视角】添加违建进度")
def add_building_progress(
    progress: schemas.BuildingProgressCreate, 
    db: Session = Depends(get_db)
):
    """
    [新增需求] 业主/巡查员操作：上传违建行为进度。
    - 用于记录“抢建”、“停工”等现场物理状态。
    - **自动化**: 自动更新案件主状态。
    """
    return case_service.add_building_progress_service(db=db, progress_data=progress)


# ==========================================
# D. 结案接口
# ==========================================

# 暂时保留 Conclusion 相关的接口占位，需确保 schema 和 crud 存在
# @case_router.post("/conclusions", ...