# 导入 datetime 模块，用于处理日期和时间对象
from datetime import date, datetime
# 导入 Python 的 Optional 类型，用于表示字段可能为空 (None)
from typing import List, Optional

# 从 sqlalchemy 库中导入核心组件
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, Text, func
# 从 sqlalchemy.orm 导入 ORM 映射相关的工具
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# 定义基类，所有的数据表模型都将继承这个类
# 这是 SQLAlchemy 2.0 的新标准写法
class Base(DeclarativeBase):
    pass

# ==========================================
# 1. 地理位置表 (Geolocation)
# 功能：存储案件发生的具体地点坐标和地址信息
# ==========================================
class Geolocation(Base):
    # 定义数据库中的表名为 'geolocations'
    __tablename__ = "geolocations"

    # 定义主键 ID，整数类型，自增
    # primary_key=True: 设为主键
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 定义详细地址，字符串类型，最大长度 255，不可为空
    address: Mapped[str] = mapped_column(String(255), comment="详细地址")
    
    # 定义经度，浮点数类型，不可为空 (用于地图定位)
    longitude: Mapped[float] = mapped_column(Float, comment="经度")
    
    # 定义纬度，浮点数类型，不可为空 (用于地图定位)
    latitude: Mapped[float] = mapped_column(Float, comment="纬度")
    
    # 定义所属社区，字符串类型，最大长度 100，不可为空
    community: Mapped[str] = mapped_column(String(100), comment="所属社区")
    
    # 定义门牌号，字符串类型，最大长度 50，不可为空
    address_number: Mapped[str] = mapped_column(String(50), comment="门牌号")

    # 定义创建时间，DateTime 类型
    # server_default=func.now(): 插入数据时，数据库自动填入当前时间
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")

    # 定义与 ViolationCase (案件表) 的反向关系
    # back_populates="location": 指向 Case 表中的 location 属性
    # uselist=False: 表示这是一对一关系 (一个位置对应一个案件)
    case: Mapped["ViolationCase"] = relationship(back_populates="location", uselist=False)


# ==========================================
# 2. 违建案件主表 (ViolationCase)
# 功能：系统的核心表，存储案件的所有基础信息
# ==========================================
class ViolationCase(Base):
    # 定义数据库中的表名为 'violation_cases'
    __tablename__ = "violation_cases"

    # 定义主键 ID
    id: Mapped[int] = mapped_column(primary_key=True)

    # --- 外键关联 ---
    # 定义外键，关联 geolocations 表的 id 字段
    # nullable=False: 案件必须绑定一个位置，不能悬空
    geolocation_id: Mapped[int] = mapped_column(ForeignKey("geolocations.id"), nullable=False)

    # --- 核心业务字段 ---
    # 定义案件编号，字符串，唯一索引 (unique=True)
    # index=True: 建立普通索引，加快查询速度
    case_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="案件编号")
    
    # 定义案件状态，如：进行中、限拆阶段、结案
    status: Mapped[str] = mapped_column(String(50), default="进行中", index=True, comment="当前状态")
    
    # 定义当事人/建设单位
    construction_unit: Mapped[str] = mapped_column(String(255), comment="当事人/单位")
    
    # 定义违建类型，如：存量违建、新增违建
    building_type: Mapped[str] = mapped_column(String(50), comment="违建类型")

    # --- 面积数据 (使用 Float 或 Numeric) ---
    # 占地面积，默认 0.0
    land_area: Mapped[float] = mapped_column(Float, default=0.0, comment="占地面积")
    # 建筑面积，默认 0.0
    building_area: Mapped[float] = mapped_column(Float, default=0.0, comment="建筑面积")
    # 违建面积，默认 0.0
    violation_area: Mapped[float] = mapped_column(Float, default=0.0, comment="违建面积")

    # --- 详细属性 (对应图片中的字段) ---
    # 办证情况 (有证/无证)
    permit_status: Mapped[str] = mapped_column(String(50), default="无证", comment="办证情况")
    # 土地性质 (集体土地/国有土地)
    land_type: Mapped[str] = mapped_column(String(50), comment="土地性质")
    # 工程类别 (砖混/钢结构等)
    engineering_category: Mapped[str] = mapped_column(String(50), comment="工程类别")
    # 案件来源 (巡查发现/举报)
    case_source: Mapped[str] = mapped_column(String(50), comment="案件来源")
    # 违建原因 (Text 类型支持长文本)
    violation_reason: Mapped[Optional[str]] = mapped_column(Text, comment="违建原因")

    # --- 日期信息 ---
    # 开工日期 (使用 Date 类型，只存年月日)
    start_date: Mapped[Optional[date]] = mapped_column(Date, comment="开工日期")
    # 发现日期
    discovery_date: Mapped[Optional[date]] = mapped_column(Date, comment="发现日期")

    # --- 系统字段 ---
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # 更新时间
    # onupdate=func.now(): 每次数据变动时，自动更新此字段
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # --- 关系定义 ---
    # 1. 关联位置表
    location: Mapped["Geolocation"] = relationship(back_populates="case")
    
    # 2. 关联执法记录表 (一对多)
    # cascade="all, delete-orphan": 如果删除了这个案件，它的所有执法记录也会被自动删除
    enforcement_actions: Mapped[List["EnforcementAction"]] = relationship(
        back_populates="case", 
        cascade="all, delete-orphan"
    )

    # 3. 关联档案表 (一对多)
    archives: Mapped[List["FileArchive"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan"
    )


# ==========================================
# 3. 执法记录/进度表 (EnforcementAction)
# 功能：记录案件的每一次推进动作（如：下达通知书、强拆）
# ==========================================
class EnforcementAction(Base):
    # 定义表名
    __tablename__ = "enforcement_actions"

    # 主键 ID
    id: Mapped[int] = mapped_column(primary_key=True)

    # 外键：关联到具体的案件 ID
    case_id: Mapped[int] = mapped_column(ForeignKey("violation_cases.id"), nullable=False)

    # 执法阶段名称 (例如：下达限期拆除通知书)
    demolition_stage: Mapped[str] = mapped_column(String(100), comment="执法阶段")
    
    # 执行人 (例如：张三、执法一队)
    demolition_guys: Mapped[str] = mapped_column(String(100), comment="执行人")
    
    # 执行日期
    demolition_date: Mapped[date] = mapped_column(Date, default=func.now(), comment="执行日期")
    
    # 状态快照：记录这一步执行完后，案件变成什么状态了 (例如：限拆阶段)
    status_snapshot: Mapped[str] = mapped_column(String(50), comment="状态变更快照")
    
    # 是否完成 (布尔值)
    is_completed: Mapped[bool] = mapped_column(default=True, comment="是否完成")

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系定义：指回主案件
    case: Mapped["ViolationCase"] = relationship(back_populates="enforcement_actions")


# ==========================================
# 4. 档案统计/文件表 (FileArchive)
# 功能：存储与案件相关的文件路径、公文号等 (对应图片第4张表)
# ==========================================
class FileArchive(Base):
    # 定义表名
    __tablename__ = "file_archives"

    # 主键 ID
    id: Mapped[int] = mapped_column(primary_key=True)

    # 外键：关联案件
    case_id: Mapped[int] = mapped_column(ForeignKey("violation_cases.id"), nullable=False)
    
    # (可选) 外键：关联某一次具体的执法记录
    # nullable=True: 文件可以只属于案件，不属于特定执法动作
    enforcement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("enforcement_actions.id"), nullable=True)

    # 文件名称
    file_name: Mapped[str] = mapped_column(String(255), comment="文件名称")
    
    # 文件存储路径 (不要存文件本身进数据库，存路径！)
    file_path: Mapped[str] = mapped_column(String(500), comment="文件存储路径")
    
    # 文件类型 (图片、PDF、Word)
    file_type: Mapped[str] = mapped_column(String(50), comment="文件类型")
    
    # 文书编号 (例如：杭违建拆字[2025]第01号)
    document_code: Mapped[Optional[str]] = mapped_column(String(100), comment="文书编号")

    # 上传时间
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系定义：指回主案件
    case: Mapped["ViolationCase"] = relationship(back_populates="archives")