# models/schemas.py

# =============================================================================
# 导入标准库模块
# =============================================================================
from datetime import date, datetime
from typing import List, Optional

# =============================================================================
# 导入 Pydantic 核心组件 (Pydantic V2)
# =============================================================================
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

# =============================================================================
# 0. 基础前置模型 (解决循环引用)
# =============================================================================

class ViolationCaseBrief(BaseModel):
    """
    [简要信息模型] 
    用于在 GeolocationRead 中展示该位置下的案件列表。
    避免包含 'location' 字段，防止死循环 (Location -> Case -> Location)。
    """
    id: int = Field(..., description="案件ID")
    case_number: str = Field(..., description="案件编号")
    status: str = Field(..., description="当前状态")
    construction_unit: str = Field(..., description="当事人/单位")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 1. 违建进度/现场 Schema (BuildingProgress)
# =============================================================================

class BuildingProgressBase(BaseModel):
    """
    [基类] 违建现场进度共享字段
    """
    description: str = Field(..., description="违建状态描述", examples=["墙体已砌筑1.5米"])
    inspector: str = Field(..., description="巡查员", examples=["王五"])
    discovery_date: date = Field(..., description="发现/记录日期")
    photo_path: Optional[str] = Field(None, description="现场照片路径")
    status_snapshot: Optional[str] = Field(None, description="状态快照")

class BuildingProgressCreate(BuildingProgressBase):
    """[创建]"""
    case_id: int = Field(..., description="关联案件ID")

class BuildingProgressRead(BuildingProgressBase):
    """[读取]"""
    id: int = Field(..., description="记录ID")
    created_at: datetime = Field(..., description="创建时间")
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 2. 执法动作 Schema (EnforcementAction)
# =============================================================================

class EnforcementActionBase(BaseModel):
    """
    [基类] 执法记录共享字段
    """
    action_stage: str = Field(..., description="执法阶段", examples=["下达限期拆除通知书"])
    executor: str = Field(..., description="执行人", examples=["执法一队"])
    action_date: date = Field(..., description="执行日期")
    status_snapshot: Optional[str] = Field(None, description="状态变更快照")

class EnforcementActionCreate(EnforcementActionBase):
    """[创建]"""
    case_id: int = Field(..., description="关联案件ID")

class EnforcementActionRead(EnforcementActionBase):
    """[读取]"""
    id: int = Field(..., description="记录ID")
    case_id: int = Field(..., description="关联案件ID")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 3. 档案文件 Schema (FileArchive)
# =============================================================================

class FileArchiveBase(BaseModel):
    """[基类]"""
    file_name: str = Field(..., description="文件名称")
    file_path: str = Field(..., description="存储路径")
    file_type: str = Field(..., description="文件类型")
    document_code: Optional[str] = Field(None, description="文书编号")

class FileArchiveCreate(FileArchiveBase):
    """[创建]"""
    case_id: int = Field(..., description="关联案件ID")
    enforcement_id: Optional[int] = Field(None, description="关联执法记录ID")

class FileArchiveRead(FileArchiveBase):
    """[读取]"""
    id: int = Field(..., description="文件ID")
    uploaded_at: datetime = Field(..., description="上传时间")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 4. 地理位置 Schema (Geolocation)
# =============================================================================

class GeolocationBase(BaseModel):
    """[基类]"""
    address: str = Field(..., description="详细地址")
    longitude: float = Field(..., description="经度")
    latitude: float = Field(..., description="纬度")
    community: str = Field(..., description="所属社区")
    address_number: str = Field(..., description="门牌号")

class GeolocationCreate(GeolocationBase):
    """[创建]"""
    pass

class GeolocationRead(GeolocationBase):
    """[读取]"""
    id: int = Field(..., description="位置ID")
    created_at: datetime = Field(..., description="创建时间")
    
    # [关键修复] 确保 ViolationCaseBrief 在此前已定义
    cases: List[ViolationCaseBrief] = []

    model_config = ConfigDict(from_attributes=True)

# [兼容性别名] 地理位置 (防止 db/crud.py 引用 LocationCreate 报错)
LocationBase = GeolocationBase
LocationCreate = GeolocationCreate
LocationRead = GeolocationRead


# =============================================================================
# 5. 违建案件 Schema (ViolationCase)
# =============================================================================

class ViolationCaseBase(BaseModel):
    """[基类]"""
    case_number: str = Field(..., description="案件编号")
    status: str = Field("进行中", description="当前状态")
    construction_unit: str = Field(..., description="当事人/单位")
    building_type: str = Field(..., description="违建类型")
    
    # 面积数据
    land_area: float = Field(0.0, description="占地面积")
    building_area: float = Field(0.0, description="建筑面积")
    violation_area: float = Field(0.0, description="违建面积")
    
    # 详细属性
    permit_status: str = Field("无证", description="办证情况")
    land_type: Optional[str] = Field(None, description="土地性质")
    engineering_category: Optional[str] = Field(None, description="工程类别")
    case_source: Optional[str] = Field(None, description="案件来源")
    violation_reason: Optional[str] = Field(None, description="违建原因")
    
    # 日期
    start_date: Optional[date] = Field(None, description="开工日期")
    discovery_date: Optional[date] = Field(None, description="发现日期")

    # [校验逻辑 1] 数值不能为负
    @field_validator('land_area', 'building_area', 'violation_area')
    def check_positive_number(cls, v):
        if v < 0:
            raise ValueError('面积数值不能为负数')
        return v

    # [校验逻辑 2] 业务逻辑校验：占地面积 <= 建筑面积
    @model_validator(mode='after')
    def check_area_logic(self):
        # 只有当两个值都大于0时才校验，避免默认值0.0造成的误判
        if self.land_area > 0 and self.building_area > 0:
            if self.land_area > self.building_area:
                raise ValueError(f'数据校验失败: 占地面积({self.land_area}) 不能大于 建筑面积({self.building_area})')
        return self


class ViolationCaseCreate(ViolationCaseBase):
    """[创建]"""
    geolocation_id: int = Field(..., description="关联的地理位置ID")


class ViolationCaseUpdate(BaseModel):
    """[更新]"""
    case_number: Optional[str] = None
    status: Optional[str] = None
    construction_unit: Optional[str] = None
    land_area: Optional[float] = None
    building_area: Optional[float] = None
    # ... 其他需要更新的字段可以继续添加 ...


class ViolationCaseList(ViolationCaseBase):
    """
    [列表模式]
    用于列表页，包含位置详情，但不包含繁重的子表数据(执法记录/现场照片)
    """
    id: int = Field(..., description="案件ID")
    geolocation_id: int = Field(..., description="地理位置ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 嵌套显示位置信息
    # 注意：这里的 GeolocationRead 里面包含了 cases 列表，
    # 如果列表数据量极大，建议后续拆分为 GeolocationSimple
    location: Optional[GeolocationRead] = None

    model_config = ConfigDict(from_attributes=True)


class ViolationCaseDetail(ViolationCaseList):
    """
    [详情模式]
    包含所有关联数据：执法记录 + 现场进度 + 档案文件
    """
    # [修改点] 双视角数据展示
    
    # 1. 政府/执法侧记录
    enforcement_actions: List[EnforcementActionRead] = []
    
    # 2. [新增] 业主/现场侧记录
    building_progresses: List[BuildingProgressRead] = []
    
    # 3. 文件档案
    archives: List[FileArchiveRead] = []

    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# 6. 结案归档 Schema (Conclusion) - [新增]
# =============================================================================

class ConclusionBase(BaseModel):
    """
    [基类] 结案信息
    """
    conclusion_date: date = Field(..., description="结案日期")
    conclusion_type: str = Field(..., description="结案类型", examples=["强制拆除", "自行拆除", "补办手续"])
    remarks: Optional[str] = Field(None, description="备注")

class ConclusionCreate(ConclusionBase):
    """[创建]"""
    case_id: int = Field(..., description="关联案件ID")

class ConclusionRead(ConclusionBase):
    """[读取]"""
    id: int = Field(..., description="记录ID")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)

# [兼容性别名] 案件 (防止 db/crud.py 引用 CaseCreate 报错)
CaseBase = ViolationCaseBase
CaseCreate = ViolationCaseCreate
CaseUpdate = ViolationCaseUpdate
CaseList = ViolationCaseList
CaseDetail = ViolationCaseDetail
CaseOut = ViolationCaseList # 兼容旧代码中的 CaseOut

# [新增：兼容性别名] 执法记录 (防止 db/crud.py 引用 DemolitionCreate 报错)
DemolitionBase = EnforcementActionBase
DemolitionCreate = EnforcementActionCreate
DemolitionRead = EnforcementActionRead
DemolitionOut = EnforcementActionRead

# [新增：兼容性别名] 违建进度 (防止 db/crud.py 引用 ViolationProgressCreate 报错)
ViolationProgressBase = BuildingProgressBase
ViolationProgressCreate = BuildingProgressCreate
ViolationProgressRead = BuildingProgressRead
ViolationProgressOut = BuildingProgressRead

# [新增：兼容性别名] 结案 (防止 db/crud.py 引用 ConclusionOut 报错)
ConclusionOut = ConclusionRead