# =============================================================================
# 导入标准库模块
# =============================================================================
# datetime: 用于处理具体的日期和时间 (例如: 2025-12-25 14:00:00)
from datetime import date, datetime
# typing: 用于类型提示，List 表示列表，Optional 表示字段可为空
from typing import List, Optional

# =============================================================================
# 导入 Pydantic 核心组件 (Pydantic V2 版本)
# =============================================================================
# BaseModel: 所有 Schema 模型的基类，提供数据验证功能
# Field: 用于定义字段的详细属性 (描述、默认值、示例值、最大长度等)
# ConfigDict: 用于配置 Pydantic 模型的行为 (如开启 ORM 模式)
# field_validator: 用于编写自定义的数据校验函数 (如检查数值不能为负)
from pydantic import BaseModel, Field, ConfigDict, field_validator


# =============================================================================
# 1. 地理位置 Schema (Geolocation)
# 功能：定义位置信息的输入输出格式
# =============================================================================

class GeolocationBase(BaseModel):
    """
    [基类] 定义地理位置的共享字段
    用于被 Create 和 Read 模型继承，避免代码重复
    """
    # 详细地址，必填，字符串类型。Field(...) 表示该字段是必填项
    address: str = Field(..., description="详细地址", examples=["幸福路88号"])
    
    # 经度，必填，浮点数。用于地图打点
    longitude: float = Field(..., description="经度", examples=[120.15515])
    
    # 纬度，必填，浮点数。用于地图打点
    latitude: float = Field(..., description="纬度", examples=[30.27415])
    
    # 所属社区，必填，字符串
    community: str = Field(..., description="所属社区", examples=["西湖社区"])
    
    # 门牌号，必填，字符串
    address_number: str = Field(..., description="门牌号", examples=["1-101"])


class GeolocationCreate(GeolocationBase):
    """
    [创建模型] 用户录入位置时使用
    """
    # 只需要继承基类的字段即可，因为创建时不需要 ID 和 创建时间
    pass


class GeolocationRead(GeolocationBase):
    """
    [读取模型] 返回给前端的数据格式
    """
    # 数据库生成的唯一 ID，前端需要用它来关联案件
    id: int = Field(..., description="位置ID")
    
    # 创建时间，数据库自动生成
    created_at: datetime = Field(..., description="创建时间")

    # 配置项：开启 ORM 模式
    # 允许 Pydantic 直接从 SQLAlchemy 对象读取数据，而不需要手动转成字典
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 2. 执法记录 Schema (EnforcementAction)
# 功能：定义执法过程的输入输出格式
# 注意：必须定义在 ViolationCase 之前，因为案件详情里需要嵌套显示它
# =============================================================================

class EnforcementActionBase(BaseModel):
    """
    [基类] 执法记录共享字段
    """
    # 执法阶段名称，例如：下达限期拆除通知书
    demolition_stage: str = Field(..., description="执法阶段")
    
    # 执行人，例如：张三、执法一队
    demolition_guys: str = Field(..., description="执行人")
    
    # 执行日期，只存年月日 (date 类型)
    demolition_date: date = Field(..., description="执行日期")
    
    # 状态快照，记录这一步操作后，案件变成了什么状态 (可选)
    status_snapshot: Optional[str] = Field(None, description="状态变更快照")
    
    # 是否完成，默认为 True
    is_completed: bool = Field(True, description="是否完成")


class EnforcementActionCreate(EnforcementActionBase):
    """
    [创建模型] 添加一条执法记录时使用
    """
    # 必须指明这条记录属于哪个案件 (外键关联)
    case_id: int = Field(..., description="关联的案件ID")


class EnforcementActionRead(EnforcementActionBase):
    """
    [读取模型] 返回给前端显示的执法记录
    """
    # 记录本身的 ID
    id: int = Field(..., description="记录ID")
    
    # 关联的案件 ID
    case_id: int = Field(..., description="关联案件ID")
    
    # 记录创建的具体时间 (包含时分秒)
    created_at: datetime = Field(..., description="创建时间")

    # 开启 ORM 模式
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 3. 档案文件 Schema (FileArchive)
# 功能：定义文件附件的输入输出格式
# =============================================================================

class FileArchiveBase(BaseModel):
    """
    [基类] 文件共享字段
    """
    # 文件名，例如：现场照片.jpg
    file_name: str = Field(..., description="文件名称")
    
    # 文件存储路径 (相对路径或URL)，例如：/uploads/2025/01/xxx.jpg
    file_path: str = Field(..., description="存储路径")
    
    # 文件类型，例如：image, pdf, word
    file_type: str = Field(..., description="文件类型")
    
    # 文书编号，可选字段
    document_code: Optional[str] = Field(None, description="文书编号")


class FileArchiveCreate(FileArchiveBase):
    """
    [创建模型] 上传文件记录时使用
    """
    # 必填：关联的案件 ID
    case_id: int = Field(..., description="关联案件ID")
    
    # 选填：关联的执法记录 ID (如果是某个阶段产生的文件)
    enforcement_id: Optional[int] = Field(None, description="关联执法记录ID")


class FileArchiveRead(FileArchiveBase):
    """
    [读取模型] 返回给前端的文件信息
    """
    # 文件记录 ID
    id: int = Field(..., description="文件ID")
    
    # 上传时间
    uploaded_at: datetime = Field(..., description="上传时间")

    # 开启 ORM 模式
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 4. 违建案件 Schema (ViolationCase)
# 功能：定义核心案件的输入输出格式
# =============================================================================

class ViolationCaseBase(BaseModel):
    """
    [基类] 案件核心共享字段
    """
    # 案件编号，必填，作为业务唯一标识
    case_number: str = Field(..., description="案件编号", examples=["20250001"])
    
    # 当前状态，默认为"进行中"
    status: str = Field("进行中", description="当前状态")
    
    # 当事人/建设单位，必填
    construction_unit: str = Field(..., description="当事人/单位")
    
    # 违建类型，必填 (存量/新增)
    building_type: str = Field(..., description="违建类型")
    
    # --- 面积数据 (默认为 0.0，避免前端不传报错) ---
    land_area: float = Field(0.0, description="占地面积")
    building_area: float = Field(0.0, description="建筑面积")
    violation_area: float = Field(0.0, description="违建面积")
    
    # --- 详细属性 (全部可选，避免录入时负担过重) ---
    permit_status: str = Field("无证", description="办证情况")
    land_type: Optional[str] = Field(None, description="土地性质")
    engineering_category: Optional[str] = Field(None, description="工程类别")
    case_source: Optional[str] = Field(None, description="案件来源")
    violation_reason: Optional[str] = Field(None, description="违建原因")
    
    # --- 日期信息 (可选) ---
    start_date: Optional[date] = Field(None, description="开工日期")
    discovery_date: Optional[date] = Field(None, description="发现日期")

    # --- 自定义校验逻辑 (Validator) ---
    @field_validator('land_area', 'building_area', 'violation_area')
    def check_positive_area(cls, v):
        """
        验证器：确保所有的面积字段不能为负数
        如果前端传了 -100，后端会直接返回 422 错误
        """
        if v < 0:
            raise ValueError('面积数据不能为负数')
        return v


class ViolationCaseCreate(ViolationCaseBase):
    """
    [创建模型] 用户新建案件时使用
    """
    # 核心约束：创建案件时，必须先创建位置，并传入位置 ID
    geolocation_id: int = Field(..., description="关联的地理位置ID")


class ViolationCaseUpdate(BaseModel):
    """
    [更新模型] 用户修改案件时使用 (PATCH)
    所有字段均为 Optional，允许只修改其中某一项，而不影响其他项
    """
    case_number: Optional[str] = None
    status: Optional[str] = None
    construction_unit: Optional[str] = None
    building_type: Optional[str] = None
    land_area: Optional[float] = None
    building_area: Optional[float] = None
    violation_area: Optional[float] = None
    permit_status: Optional[str] = None
    # ... 这里的字段应该覆盖 Base 中所有可修改的字段 ...


class ViolationCaseList(ViolationCaseBase):
    """
    [读取模型 - 列表模式]
    用于案件列表页展示，只包含基础信息，不包含执法记录等重数据
    """
    # 案件 ID
    id: int = Field(..., description="案件ID")
    
    # 关联的位置 ID
    geolocation_id: int = Field(..., description="地理位置ID")
    
    # 创建时间
    created_at: datetime = Field(..., description="创建时间")
    
    # 更新时间
    updated_at: datetime = Field(..., description="更新时间")
    
    # 嵌套显示：返回位置的详细信息 (一对一)
    # 这样前端可以在列表里直接显示地址，不用再查一次
    location: Optional[GeolocationRead] = None

    # 开启 ORM 模式
    model_config = ConfigDict(from_attributes=True)


class ViolationCaseDetail(ViolationCaseList):
    """
    [读取模型 - 详情模式]
    用于案件详情页展示，包含所有关联数据 (执法记录、档案文件)
    继承自 List 模型，所以自动拥有了 ID、Location 等信息
    """
    # 嵌套显示：该案件下的所有执法记录列表
    enforcement_actions: List[EnforcementActionRead] = []
    
    # 嵌套显示：该案件下的所有文件列表
    archives: List[FileArchiveRead] = []

    # 开启 ORM 模式
    model_config = ConfigDict(from_attributes=True)