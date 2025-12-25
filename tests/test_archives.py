# tests/test_archives.py

from fastapi.testclient import TestClient

def test_archive_compliance_missing_docs(client: TestClient):
    """
    【接口测试】档案合规性检查
    场景：案件进入"限期拆除"阶段，但未上传任何文件。
    预期：
    1. 接口返回 200 OK
    2. is_compliant 为 False
    3. missing_docs 列表包含配置中要求的关键文件
    """
    # ---------------------------------------------------------
    # 1. 准备数据：创建位置 -> 创建案件
    # ---------------------------------------------------------
    loc_resp = client.post("/api/locations/", json={
        "address": "档案测试路", "longitude": 0, "latitude": 0, "community": "A", "address_number": "1"
    })
    assert loc_resp.status_code == 201
    loc_id = loc_resp.json()["id"]

    # 【关键修复】：补全 land_type, engineering_category, case_source 等必填字段
    # 虽然 Schema 里它们是 Optional，但在数据库 Model 里它们是 NOT NULL
    case_payload = {
        "geolocation_id": loc_id,
        "construction_unit": "档案测试户",
        "building_type": "存量",
        "case_number": "ARCHIVE_TEST",
        "land_area": 10, 
        "building_area": 20,
        # --- 补全必填字段 ---
        "land_type": "国有土地",
        "engineering_category": "砖混",
        "case_source": "巡查发现"
    }

    case_resp = client.post("/api/cases/", json=case_payload)
    assert case_resp.status_code == 201, f"创建案件失败: {case_resp.text}"
    case_id = case_resp.json()["id"]

    # ---------------------------------------------------------
    # 2. 变更状态：将案件推送到 "限期拆除" 阶段
    #    (因为我们在配置里定义了该阶段需要有文件)
    # ---------------------------------------------------------
    # 这里的 status_snapshot 必须严格匹配 REQUIRED_DOC_RULES 的 key
    client.post("/api/cases/enforcement", json={
        "case_id": case_id,
        "action_stage": "下达文书",
        "executor": "执法队",
        "action_date": "2025-01-01",
        "status_snapshot": "限期拆除"  
    })

    # ---------------------------------------------------------
    # 3. 调用检查接口
    # ---------------------------------------------------------
    resp = client.get(f"/api/cases/{case_id}/archive-check")
    assert resp.status_code == 200
    
    result = resp.json()

    # ---------------------------------------------------------
    # 4. 验证核心逻辑
    # ---------------------------------------------------------
    # 断言当前阶段识别正确
    assert result["current_stage"] == "限期拆除"
    
    # 断言不合规 (因为我们没上传任何文件)
    assert result["is_compliant"] is False
    
    # 断言确实返回了缺失文件列表
    # (根据你之前的配置，应该包含 "责令停止违法行为决定书")
    assert isinstance(result["missing_docs"], list)
    assert len(result["missing_docs"]) > 0
    # 只要缺失列表里包含任意一个关键文件即可证明逻辑生效
    assert "责令停止违法行为决定书" in result["missing_docs"]


def test_create_case_negative_input(client: TestClient):
    """
    【边界测试】非法输入
    场景：尝试创建案件时输入负数的 violation_area
    预期：Pydantic 校验失败，返回 422 Unprocessable Entity
    """
    # 先建个位置
    loc_id = client.post("/api/locations/", json={
        "address": "负数测试", "longitude": 0, "latitude": 0, "community": "A", "address_number": "1"
    }).json()["id"]

    # 这里虽然也缺了 land_type 等必填项，但因为 violation_area 是负数，
    # Pydantic 在数据验证阶段（入库前）就会直接抛出 ValidationError (422)，
    # 所以程序根本跑不到数据库插入那一步，因此不会报 IntegrityError。
    bad_payload = {
        "geolocation_id": loc_id,
        "construction_unit": "负数人",
        "building_type": "存量",
        "case_number": "NEG_001",
        "land_area": 10.0,
        "building_area": 10.0,
        "violation_area": -50.0  # <--- 非法输入：违建面积为负
    }

    resp = client.post("/api/cases/", json=bad_payload)
    
    # FastAPI/Pydantic 的默认校验错误码是 422
    assert resp.status_code == 422
    
    # 验证错误详情里是否提到了 violation_area
    error_detail = resp.json()["detail"]
    # 只要找到有关 violation_area 的报错即可
    found = False
    for err in error_detail:
        if "violation_area" in err["loc"]:
            found = True
            break
    assert found


def test_action_on_nonexistent_case(client: TestClient):
    """
    【边界测试】404 错误
    场景：向不存在的 case_id 添加执法记录
    预期：返回 404 Not Found
    """
    non_existent_id = 999999
    
    payload = {
        "case_id": non_existent_id,
        "action_stage": "虚空执法",
        "executor": "幽灵",
        "action_date": "2025-01-01",
        "status_snapshot": "无"
    }

    resp = client.post("/api/cases/enforcement", json=payload)
    
    assert resp.status_code == 404
    assert resp.json()["detail"] == "关联的案件不存在"