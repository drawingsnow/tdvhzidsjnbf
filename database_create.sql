-- ============================================
-- 政府违建案件管理系统数据库建表脚本
-- 数据库：violation_management
-- 字符集：utf8mb4
-- 引擎：InnoDB
-- ============================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS violation_management 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE violation_management;

-- ============================================
-- 表：geographical_location (地理位置表)
-- 用途：存储违建案件的地理位置信息，包括社区、门牌号、经纬度坐标
-- ============================================
CREATE TABLE IF NOT EXISTS geographical_location (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID，自增',
    community VARCHAR(100) NOT NULL COMMENT '社区/村',
    address_number VARCHAR(50) NOT NULL COMMENT '门牌号',
    latitude DECIMAL(10,8) NOT NULL COMMENT '纬度',
    longitude DECIMAL(11,8) NOT NULL COMMENT '经度',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_community (community) COMMENT '社区索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='地理位置信息表';


-- ============================================
-- 表：violation_case (违建案件表)
-- 用途：存储违建案件的核心信息，包括建筑类型、面积、违建原因等
-- ============================================
CREATE TABLE IF NOT EXISTS violation_case (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID，自增',
    building_type VARCHAR(255) NOT NULL COMMENT '建筑类型（如"自建房""别墅"）',
    geolocation_id INT NOT NULL COMMENT '地理位置ID（外键）',
    construction_unit VARCHAR(255) NOT NULL COMMENT '建设单位',
    land_area DECIMAL(10,2) NOT NULL COMMENT '占地面积（平方米）',
    building_area DECIMAL(10,2) NOT NULL COMMENT '建筑面积（平方米）',
    violation_area DECIMAL(10,2) NOT NULL COMMENT '违建面积（平方米）',
    start_date DATE NOT NULL COMMENT '开工时间',
    permit_status VARCHAR(255) NOT NULL COMMENT '报建情况（如"已报建""未报建"）',
    discovery_date DATE NOT NULL COMMENT '发现日期',
    land_type VARCHAR(255) NOT NULL COMMENT '土地性质（如"宅基地""商业用地"）',
    violation_reason TEXT NOT NULL COMMENT '违建原因',
    case_source VARCHAR(255) NOT NULL COMMENT '案件来源（如"巡查发现""群众举报"）',
    engineering_category VARCHAR(255) NOT NULL COMMENT '工程类别（如"住宅""工业"）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_geolocation (geolocation_id) COMMENT '地理位置索引',
    INDEX idx_discovery_date (discovery_date) COMMENT '发现日期索引',
    status VARCHAR(10) NOT NULL COMMENT '案件状态（如"进行中""已结案"）',
    CONSTRAINT fk_violation_case_geolocation 
        FOREIGN KEY (geolocation_id) 
        REFERENCES geographical_location(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='违建案件信息表';



-- ============================================
-- 表：demolition_progress (拆除进度表)
-- 用途：记录违建案件的拆除进度，包括各个拆除阶段的执行情况
-- ============================================
CREATE TABLE IF NOT EXISTS demolition_progress (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID，自增',
    case_id INT NOT NULL COMMENT '案件ID（外键）',
    demolition_stage VARCHAR(100) NOT NULL COMMENT '拆除阶段（如"发责令停止通知书""停水停电""发强制拆除通知书""实施强制拆除"）',
    demolition_date DATE NULL COMMENT '执行日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_case_id (case_id) COMMENT '案件ID索引',
    INDEX idx_demolition_date (demolition_date) COMMENT '执行日期索引',
    CONSTRAINT fk_demolition_progress_case 
        FOREIGN KEY (case_id) 
        REFERENCES violation_case(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='拆除进度表';


-- ============================================
-- 表：building_violation_progress (建筑违建状态进度表)
-- 用途：记录违建建筑的当前状态和变化进度，如主体完工、内部装修中等
-- ============================================
CREATE TABLE IF NOT EXISTS building_violation_progress (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID，自增',
    case_id INT NOT NULL COMMENT '案件ID（外键）',
    status_description TEXT NOT NULL COMMENT '状态描述（如"主体完工""内部装修中"）',
    status_date DATE NOT NULL COMMENT '记录日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_case_id (case_id) COMMENT '案件ID索引',
    INDEX idx_status_date (status_date) COMMENT '状态日期索引',
    CONSTRAINT fk_building_violation_progress_case 
        FOREIGN KEY (case_id) 
        REFERENCES violation_case(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='建筑违建状态进度表';