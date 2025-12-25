# models/sqlalchemy_model.py

from datetime import date, datetime
from typing import List, Optional

# 从 sqlalchemy 库中导入核心组件
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, Text, func
# 从 sqlalchemy.orm 导入 ORM 映射相关的工具
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# 定义基类
class Base(DeclarativeBase):
    pass

# ==========================================
# 1. 地理位置表 (Geolocation)
# 功能：存储案件发生的具体地点坐标和地址信息
# 修改：改为一对多关系，一个位置可以对应多个案件
# ==========================================
class Geolocation(Base):
    __tablename__ = "geolocations"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    address: Mapped[str] = mapped_column(String(255), comment="详细地址")
    longitude: Mapped[float] = mapped_column(Float, comment="经度")
    latitude: Mapped[float] = mapped_column(Float, comment="纬度")
    community: Mapped[str] = mapped_column(String(100), comment="所属社区")
    address_number: Mapped[str] = mapped_column(String(50), comment="门牌号")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")

    # [修改点]：一对多关系
    # back_populates 指向 ViolationCase 中的 location 字段
    # 类型改为 List["ViolationCase"]，移除了 uselist=False
    cases: Mapped[List["ViolationCase"]] = relationship(back_populates="location")


# ==========================================
# 2. 违建案件主表 (ViolationCase)
# 功能：系统的核心表，存储案件的所有基础信息
# ==========================================
class ViolationCase(Base):
    __tablename__ = "violation_cases"

    id: Mapped[int] = mapped_column(primary_key=True)

    # --- 外键关联 ---
    geolocation_id: Mapped[int] = mapped_column(ForeignKey("geolocations.id"), nullable=False)

    # --- 核心业务字段 ---
    case_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="案件编号")
    status: Mapped[str] = mapped_column(String(50), default="进行中", index=True, comment="当前状态")
    construction_unit: Mapped[str] = mapped_column(String(255), comment="当事人/单位")
    building_type: Mapped[str] = mapped_column(String(50), comment="违建类型")

    # --- 面积数据 ---
    land_area: Mapped[float] = mapped_column(Float, default=0.0, comment="占地面积")
    building_area: Mapped[float] = mapped_column(Float, default=0.0, comment="建筑面积")
    violation_area: Mapped[float] = mapped_column(Float, default=0.0, comment="违建面积")

    # --- 详细属性 ---
    permit_status: Mapped[str] = mapped_column(String(50), default="无证", comment="办证情况")
    land_type: Mapped[str] = mapped_column(String(50), comment="土地性质")
    engineering_category: Mapped[str] = mapped_column(String(50), comment="工程类别")
    case_source: Mapped[str] = mapped_column(String(50), comment="案件来源")
    violation_reason: Mapped[Optional[str]] = mapped_column(Text, comment="违建原因")

    # --- 日期信息 ---
    start_date: Mapped[Optional[date]] = mapped_column(Date, comment="开工日期")
    discovery_date: Mapped[Optional[date]] = mapped_column(Date, comment="发现日期")

    # --- 系统字段 ---
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # --- 关系定义 ---
    
    # 1. 关联位置表 (多对一)
    location: Mapped["Geolocation"] = relationship(back_populates="cases")
    
    # 2. 关联执法动作表 (一对多) - 政府侧
    enforcement_actions: Mapped[List["EnforcementAction"]] = relationship(
        back_populates="case", 
        cascade="all, delete-orphan"
    )

    # 3. [新增] 关联违建进度表 (一对多) - 业主/现场侧
    building_progresses: Mapped[List["BuildingProgress"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan"
    )

    # 4. 关联档案表 (一对多)
    archives: Mapped[List["FileArchive"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan"
    )


# ==========================================
# 3. 执法动作表 (EnforcementAction)
# 功能：记录政府/执法部门的执行动作（如：下达通知书、催告、强拆）
# 修改：字段重命名以更贴切通用执法行为
# ==========================================
class EnforcementAction(Base):
    __tablename__ = "enforcement_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("violation_cases.id"), nullable=False)

    # 执法阶段 (原 demolition_stage)
    action_stage: Mapped[str] = mapped_column(String(100), comment="执法阶段")
    
    # 执行人 (原 demolition_guys)
    executor: Mapped[str] = mapped_column(String(100), comment="执行人")
    
    # 执行日期 (原 demolition_date)
    action_date: Mapped[date] = mapped_column(Date, default=func.now(), comment="执行日期")
    
    # 状态快照
    status_snapshot: Mapped[str] = mapped_column(String(50), comment="状态变更快照")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系定义
    case: Mapped["ViolationCase"] = relationship(back_populates="enforcement_actions")


# ==========================================
# 4. [新增] 违建进度/现场表 (BuildingProgress)
# 功能：记录业主违建行为的物理状态、巡查发现情况
# ==========================================
class BuildingProgress(Base):
    __tablename__ = "building_progresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("violation_cases.id"), nullable=False)

    # 违建状态描述 (例如：正在打地基、墙体已砌筑、已封顶)
    description: Mapped[str] = mapped_column(Text, comment="违建状态描述")
    
    # 巡查员/发现人
    inspector: Mapped[str] = mapped_column(String(100), comment="巡查员")
    
    # 发现/记录日期
    discovery_date: Mapped[date] = mapped_column(Date, default=func.now(), comment="发现日期")
    
    # 现场照片路径
    photo_path: Mapped[Optional[str]] = mapped_column(String(500), comment="现场照片路径")
    
    # 状态快照 (记录当时的案件总状态)
    status_snapshot: Mapped[str] = mapped_column(String(50), comment="状态快照")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系定义
    case: Mapped["ViolationCase"] = relationship(back_populates="building_progresses")


# ==========================================
# 5. 档案统计/文件表 (FileArchive)
# 功能：存储与案件相关的文件路径、公文号等
# ==========================================
class FileArchive(Base):
    __tablename__ = "file_archives"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("violation_cases.id"), nullable=False)
    
    # 依然可以关联到某次具体的执法动作（可选）
    enforcement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("enforcement_actions.id"), nullable=True)

    file_name: Mapped[str] = mapped_column(String(255), comment="文件名称")
    file_path: Mapped[str] = mapped_column(String(500), comment="文件存储路径")
    file_type: Mapped[str] = mapped_column(String(50), comment="文件类型")
    document_code: Mapped[Optional[str]] = mapped_column(String(100), comment="文书编号")

    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    case: Mapped["ViolationCase"] = relationship(back_populates="archives")