# tests/test_services.py

import pytest
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from pydantic import ValidationError  # 导入 Pydantic 校验异常

from services import case_service
from models import schemas
from models import sqlalchemy_model as models

# ==========================================
# 1. 测试案件编号生成逻辑
# ==========================================

def test_generate_case_number_increment(db_session: Session):
    """
    场景：当年已有案件，测试编号自增
    模拟：数据库已存在 20250001
    预期：生成 20250002
    """
    current_year = str(datetime.now().year)
    
    # 1. 创建位置
    loc = models.Geolocation(
        address="Test", longitude=0, latitude=0, community="C", address_number="1"
    )
    db_session.add(loc)
    db_session.commit()

    # 2. 插入已有案件
    # 【关键修正】：补全所有 Mapped[str] 的必填字段
    exist_case = models.ViolationCase(
        case_number=f"{current_year}0001",
        geolocation_id=loc.id,
        status="进行中",
        construction_unit="Existing",
        building_type="Type",
        land_area=0, building_area=0, violation_area=0,
        # --- 补全以下必填字段 ---
        land_type="国有土地",
        engineering_category="砖混",
        case_source="巡查发现"
    )
    db_session.add(exist_case)
    db_session.commit()

    # 3. 调用生成器
    new_number = case_service.generate_case_number(db_session)

    # 4. 断言
    expected_number = f"{current_year}0002"
    assert new_number == expected_number


def test_generate_case_number_new_year(db_session: Session):
    """
    场景：跨年或当年无案件
    模拟：数据库为空，或者只存在去年的案件 (例如 20200005)
    预期：从 xxxx0001 开始
    """
    current_year = str(datetime.now().year)
    
    # 1. 创建位置
    loc = models.Geolocation(
        address="Old", longitude=0, latitude=0, community="C", address_number="1"
    )
    db_session.add(loc)
    db_session.commit()

    # 2. 插入旧年份案件
    old_case = models.ViolationCase(
        case_number="20200005", # 旧年份
        geolocation_id=loc.id,
        status="结案",
        construction_unit="OldGuy",
        building_type="Type",
        # --- 补全必填字段 ---
        land_area=0, building_area=0, violation_area=0,
        land_type="国有土地",
        engineering_category="钢结构",
        case_source="举报"
    )
    db_session.add(old_case)
    db_session.commit()

    # 3. 调用生成器
    new_number = case_service.generate_case_number(db_session)

    # 4. 断言
    expected_number = f"{current_year}0001"
    assert new_number == expected_number


# ==========================================
# 2. 测试面积校验逻辑
# ==========================================

def test_create_case_area_validation(db_session: Session):
    """
    场景：创建案件时，占地面积 > 建筑面积
    预期：抛出 Pydantic ValidationError
    """
    # 由于我们在 Schema 中使用了 @model_validator
    # 错误会在实例化 Schema 时抛出，类型为 pydantic.ValidationError
    with pytest.raises(ValidationError) as excinfo:
        schemas.ViolationCaseCreate(
            geolocation_id=1,
            case_number="TEMP",
            construction_unit="Tester",
            building_type="TestType",
            land_area=100.0,      # <--- 错误：占地大
            building_area=50.0,   # <--- 错误：建筑小
            violation_area=50.0
        )
    
    # 验证错误信息包含我们写的提示
    error_msg = str(excinfo.value)
    assert "不能大于" in error_msg


# ==========================================
# 3. 测试档案清单检查 (Archive Check)
# ==========================================

def test_archive_check_missing_docs(db_session: Session):
    """
    场景：案件处于 '强制拆除' 阶段，缺失 '强制拆除决定书'
    模拟：只上传了一张 '现场照片.jpg'
    预期：is_compliant=False, missing_docs 包含相关文件
    """
    # 1. 准备基础数据
    loc = models.Geolocation(
        address="Loc", longitude=0, latitude=0, community="C", address_number="1"
    )
    db_session.add(loc)
    db_session.commit()

    target_status = "强制拆除" 
    
    case = models.ViolationCase(
        case_number="20258888",
        geolocation_id=loc.id,
        status=target_status,
        construction_unit="BadGuy",
        building_type="Type",
        # --- 补全必填字段 ---
        land_area=10, building_area=20, violation_area=10,
        land_type="集体土地",
        engineering_category="砖混",
        case_source="巡查"
    )
    db_session.add(case)
    db_session.commit()

    # 2. 模拟上传一个"不相关"的文件
    archive = models.FileArchive(
        case_id=case.id,
        file_name="无关的现场照片.jpg",
        file_path="/tmp/1.jpg",
        file_type="image"
    )
    db_session.add(archive)
    db_session.commit()

    # 3. 调用 Service 检查状态
    result = case_service.check_archive_status(db_session, case.id)

    # 4. 断言
    assert result.current_stage == target_status
    assert result.is_compliant is False
    assert len(result.missing_docs) > 0


def test_archive_check_compliant(db_session: Session):
    """
    场景：测试合规情况 (正向测试)
    """
    # 1. 准备数据
    loc = models.Geolocation(
        address="Loc2", longitude=0, latitude=0, community="C", address_number="2"
    )
    db_session.add(loc)
    db_session.commit()

    case = models.ViolationCase(
        case_number="20259999",
        geolocation_id=loc.id,
        status="强制拆除",
        construction_unit="GoodGuy",
        building_type="Type",
        # --- 补全必填字段 ---
        land_area=10, building_area=20, violation_area=10,
        land_type="国有土地",
        engineering_category="钢结构",
        case_source="举报"
    )
    db_session.add(case)
    db_session.commit()

    # 2. 上传符合要求的文件
    # 规则需要: "强制拆除现场笔录", "强制拆除现场图片"
    doc1 = models.FileArchive(case_id=case.id, file_name="2025_强制拆除现场笔录.pdf", file_path="x", file_type="pdf")
    doc2 = models.FileArchive(case_id=case.id, file_name="evidence_强制拆除现场图片_01.jpg", file_path="x", file_type="image")
    
    db_session.add_all([doc1, doc2])
    db_session.commit()

    # 3. 检查
    result = case_service.check_archive_status(db_session, case.id)

    # 4. 断言
    assert result.is_compliant is True
    assert len(result.missing_docs) == 0