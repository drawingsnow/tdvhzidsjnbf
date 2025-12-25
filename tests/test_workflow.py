# tests/test_workflow.py

from fastapi.testclient import TestClient

def test_workflow_one_location_many_cases(client: TestClient):
    """
    【场景一】测试一地多案 (1:N Location)
    1. 创建一个地理位置
    2. 关联创建两个不同的案件
    3. 反查位置，验证包含这两个案件的历史记录
    """
    # ----------------------------------------------------------------
    # Step 1: 创建地理位置
    # ----------------------------------------------------------------
    loc_payload = {
        "address": "西湖区文三路8号",
        "longitude": 120.111,
        "latitude": 30.111,
        "community": "文三社区",
        "address_number": "8-1"
    }
    resp_loc = client.post("/api/locations/", json=loc_payload)
    assert resp_loc.status_code == 201
    location_id = resp_loc.json()["id"]

    # ----------------------------------------------------------------
    # Step 2: 创建案件 A (Case A)
    # ----------------------------------------------------------------
    case_a_payload = {
        "geolocation_id": location_id, # 关联同一个 ID
        "construction_unit": "张三 (Case A)",
        "building_type": "存量",
        "case_number": "CASE_A", # 后端会自动生成覆盖，这里仅占位
        "land_area": 50.0,
        "building_area": 100.0,
        # --- 补全必填字段 ---
        "land_type": "集体土地",
        "engineering_category": "砖混",
        "case_source": "巡查发现"
    }
    resp_case_a = client.post("/api/cases/", json=case_a_payload)
    assert resp_case_a.status_code == 201, resp_case_a.text
    case_a_id = resp_case_a.json()["id"]

    # ----------------------------------------------------------------
    # Step 3: 创建案件 B (Case B)
    # ----------------------------------------------------------------
    case_b_payload = {
        "geolocation_id": location_id, # 关联同一个 ID
        "construction_unit": "李四 (Case B)",
        "building_type": "新增",
        "case_number": "CASE_B",
        "land_area": 20.0,
        "building_area": 40.0,
        # --- 补全必填字段 ---
        "land_type": "国有土地",
        "engineering_category": "钢结构",
        "case_source": "举报"
    }
    resp_case_b = client.post("/api/cases/", json=case_b_payload)
    assert resp_case_b.status_code == 201, resp_case_b.text
    case_b_id = resp_case_b.json()["id"]

    # ----------------------------------------------------------------
    # Step 4: 调用位置历史接口，验证 1:N 关系
    # ----------------------------------------------------------------
    # 访问 GET /api/locations/{id}/history
    resp_history = client.get(f"/api/locations/{location_id}/history")
    assert resp_history.status_code == 200
    
    data = resp_history.json()
    
    # 验证地址信息正确
    assert data["address"] == "西湖区文三路8号"
    
    # 验证 cases 列表里有两个案件
    cases_list = data["cases"]
    assert len(cases_list) == 2
    
    # 提取 ID 列表进行比对
    case_ids = [c["id"] for c in cases_list]
    assert case_a_id in case_ids
    assert case_b_id in case_ids
    
    # 验证当事人姓名是否正确返回（确保简要信息准确）
    units = [c["construction_unit"] for c in cases_list]
    assert "张三 (Case A)" in units
    assert "李四 (Case B)" in units


def test_workflow_dual_perspective_status_link(client: TestClient):
    """
    【场景二】测试双视角进度与状态联动
    1. 政府侧添加执法记录 -> 状态变更
    2. 业主侧添加违建进度 -> 状态变更
    3. 详情页聚合展示
    """
    # ----------------------------------------------------------------
    # Step 0: 准备数据 (创建位置和案件)
    # ----------------------------------------------------------------
    # 快速创建一个位置
    loc_id = client.post("/api/locations/", json={
        "address": "状态测试路", "longitude": 0, "latitude": 0, "community": "X", "address_number": "1"
    }).json()["id"]
    
    # 创建案件，初始状态默认为"进行中"
    case_resp = client.post("/api/cases/", json={
        "geolocation_id": loc_id,
        "construction_unit": "状态测试人",
        "building_type": "存量",
        "case_number": "STATUS_TEST",
        "land_area": 10, "building_area": 20,
        # --- 补全必填字段 ---
        "land_type": "集体土地",
        "engineering_category": "混合",
        "case_source": "卫星图斑"
    })
    assert case_resp.status_code == 201, case_resp.text
    case_id = case_resp.json()["id"]
    assert case_resp.json()["status"] == "进行中"

    # ----------------------------------------------------------------
    # Step 1: 政府侧 - 添加执法记录 (下达限期拆除通知书)
    # ----------------------------------------------------------------
    enf_payload = {
        "case_id": case_id,
        "action_stage": "下达通知",
        "executor": "执法大队",
        "action_date": "2025-05-01",
        "status_snapshot": "下达限期拆除通知书"  # <--- 期望更新的状态
    }
    resp_enf = client.post("/api/cases/enforcement", json=enf_payload)
    assert resp_enf.status_code == 200

    # 验证：立即查询案件详情，看状态是否变了
    resp_check_1 = client.get(f"/api/cases/{case_id}")
    assert resp_check_1.json()["status"] == "下达限期拆除通知书"

    # ----------------------------------------------------------------
    # Step 2: 业主侧 - 添加违建进度 (业主抢建)
    # ----------------------------------------------------------------
    prog_payload = {
        "case_id": case_id,
        "description": "连夜施工，墙体增高",
        "inspector": "网格员小王",
        "discovery_date": "2025-05-02",
        "status_snapshot": "业主抢建" # <--- 期望再次更新的状态
    }
    resp_prog = client.post("/api/cases/building-progress", json=prog_payload)
    assert resp_prog.status_code == 200

    # 验证：再次查询案件详情，看状态是否又变了
    resp_check_2 = client.get(f"/api/cases/{case_id}")
    detail = resp_check_2.json()
    
    assert detail["status"] == "业主抢建"

    # ----------------------------------------------------------------
    # Step 3: 验证详情页的双视角数据聚合
    # ----------------------------------------------------------------
    # 确保 enforcement_actions 列表里有 Step 1 的记录
    assert len(detail["enforcement_actions"]) == 1
    assert detail["enforcement_actions"][0]["action_stage"] == "下达通知"
    
    # 确保 building_progresses 列表里有 Step 2 的记录
    assert len(detail["building_progresses"]) == 1
    assert detail["building_progresses"][0]["description"] == "连夜施工，墙体增高"