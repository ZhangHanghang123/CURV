-- ============================================================================
-- 收益率曲线管理与建模分析平台 (CURV) — 数据库初始化脚本
-- 数据库：curv_db
-- 用户：almd（与 ALMD/IALMD/ALMT 共用，密码 Almd@2026，URL 中 @ 需编码为 %40）
-- 表前缀：curv_（业务表）/ sys_（系统表，沿用 ALMD）
-- 字符集：utf8mb4 / 排序：utf8mb4_unicode_ci
-- 设计版本：V1.0   日期：2026-08-17
-- ============================================================================

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS `curv_db`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `curv_db`;

-- ============================================================================
-- 第一部分：基础字典表（无业务依赖，先建）
-- ============================================================================

-- 1.1 标准期限点字典
DROP TABLE IF EXISTS `curv_tenor_standard`;
CREATE TABLE `curv_tenor_standard` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `tenor_code` varchar(16) NOT NULL COMMENT '期限编码：1D/7D/1M/3M/6M/9M/1Y/2Y/3Y/5Y/7Y/10Y/15Y/20Y/30Y',
  `tenor_name` varchar(32) NOT NULL COMMENT '期限名称',
  `days` int NOT NULL COMMENT '换算天数',
  `sort_order` int NOT NULL DEFAULT 0 COMMENT '排序',
  `is_active` tinyint NOT NULL DEFAULT 1 COMMENT '是否启用',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenor_code` (`tenor_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标准期限点字典';

INSERT INTO `curv_tenor_standard` (`tenor_code`,`tenor_name`,`days`,`sort_order`) VALUES
('1D','1天',1,1),('7D','7天',7,2),('14D','14天',14,3),('1M','1个月',30,4),
('3M','3个月',90,5),('6M','6个月',180,6),('9M','9个月',270,7),('1Y','1年',365,8),
('3Y','3年',365*3,9),('5Y','5年',365*5,10),('7Y','7年',365*7,11),('10Y','10年',365*10,12),
('15Y','15年',365*15,13),('20Y','20年',365*20,14),('30Y','30年',365*30,15);

-- 1.2 利率类型字典
DROP TABLE IF EXISTS `curv_rate_type_dict`;
CREATE TABLE `curv_rate_type_dict` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(32) NOT NULL COMMENT 'spot/forward/yield_par/par_yield/zero',
  `name` varchar(64) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `sort_order` int NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='利率类型字典';

INSERT INTO `curv_rate_type_dict` (`code`,`name`,`description`,`sort_order`) VALUES
('spot','即期利率','spot rate',1),
('forward','远期利率','forward rate',2),
('yield_to_maturity','到期收益率','YTM',3),
('par_yield','平价收益率','par yield',4),
('zero','零息利率','zero coupon rate',5);

-- 1.3 计息基准字典
DROP TABLE IF EXISTS `curv_day_count_dict`;
CREATE TABLE `curv_day_count_dict` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(32) NOT NULL COMMENT 'ACT/365, 30/360, ACT/360, ACT/ACT',
  `name` varchar(64) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='计息基准字典';

INSERT INTO `curv_day_count_dict` (`code`,`name`,`description`) VALUES
('ACT/365','实际天数/365','Actual/365 Fixed'),
('ACT/360','实际天数/360','Actual/360'),
('30/360','30/360','Bond Basis'),
('ACT/ACT','实际天数/实际天数','Actual/Actual');

-- 1.4 复利方式字典
DROP TABLE IF EXISTS `curv_compound_dict`;
CREATE TABLE `curv_compound_dict` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(32) NOT NULL COMMENT 'simple/compound/continuous',
  `name` varchar(64) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='复利方式字典';

INSERT INTO `curv_compound_dict` (`code`,`name`,`description`) VALUES
('simple','单利','Simple Interest'),
('compound','复利','Compound Interest'),
('continuous','连续复利','Continuously Compounded');

-- 1.5 拟合/平滑算法插件表
DROP TABLE IF EXISTS `curv_plugin_model`;
CREATE TABLE `curv_plugin_model` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(64) NOT NULL COMMENT 'nelson_siegel/svensson/cubic_spline/pchip/ewma/loess',
  `name` varchar(128) NOT NULL,
  `type` varchar(32) NOT NULL COMMENT 'fit/interpolate/smooth',
  `impl_path` varchar(255) NOT NULL COMMENT 'Python 模块路径',
  `params_schema` json DEFAULT NULL COMMENT '参数 schema（JSON）',
  `description` varchar(500) DEFAULT NULL,
  `is_enabled` tinyint NOT NULL DEFAULT 1,
  `is_builtin` tinyint NOT NULL DEFAULT 1 COMMENT '是否内置',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`),
  KEY `idx_type` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='拟合/插值/平滑算法插件';

INSERT INTO `curv_plugin_model` (`code`,`name`,`type`,`impl_path`,`params_schema`,`description`) VALUES
('nelson_siegel','Nelson-Siegel 拟合','fit','curv.engines.fitting:NelsonSiegel','{"tau":{"type":"float","default":1.5}}','三参数模型 β0/β1/β2，经济含义明确'),
('svensson','Svensson (NSS) 拟合','fit','curv.engines.fitting:Svensson','{"tau1":{"type":"float","default":1.5},"tau2":{"type":"float","default":5.0}}','四参数模型 NS+β3，适合复杂曲线'),
('cubic_spline','三次样条插值','interpolate','curv.engines.interpolation:CubicSpline','{}','scipy CubicSpline，二阶连续可导'),
('pchip','PCHIP 单调保形插值','interpolate','curv.engines.interpolation:PCHIP','{}','保持数据单调性，无过冲'),
('linear','线性插值','interpolate','curv.engines.interpolation:Linear','{}','简单快速'),
('log_linear','对数线性插值','interpolate','curv.engines.interpolation:LogLinear','{}','贴现因子插值'),
('ewma','指数加权移动平均','smooth','curv.engines.smoothing:EWMA','{"halflife":{"type":"float","default":3}}','指数平滑'),
('loess','LOESS 局部回归平滑','smooth','curv.engines.smoothing:LOESS','{"frac":{"type":"float","default":0.3}}','statsmodels lowess');


-- ============================================================================
-- 第二部分：L1 数据采集层
-- ============================================================================

-- 2.1 数据源配置
DROP TABLE IF EXISTS `curv_data_source`;
CREATE TABLE `curv_data_source` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(64) NOT NULL COMMENT 'china_bond_treasury / shibor / wind_ncd ...',
  `name` varchar(128) NOT NULL,
  `source_type` varchar(32) NOT NULL COMMENT 'API / FILE / MANUAL',
  `provider` varchar(64) DEFAULT NULL COMMENT '中债登/外汇交易中心/Wind/央行',
  `config_json` json DEFAULT NULL COMMENT 'URL/参数/认证',
  `auth_json` json DEFAULT NULL COMMENT 'API Key/OAuth2',
  `field_mapping_json` json DEFAULT NULL COMMENT '字段映射',
  `frequency` varchar(32) DEFAULT 'daily' COMMENT 'daily/intraday/manual',
  `cron_expr` varchar(64) DEFAULT NULL COMMENT 'cron 表达式',
  `is_enabled` tinyint NOT NULL DEFAULT 1,
  `last_run_time` datetime DEFAULT NULL,
  `last_run_status` varchar(32) DEFAULT NULL COMMENT 'success/failed/timeout',
  `last_run_msg` varchar(500) DEFAULT NULL,
  `status` tinyint NOT NULL DEFAULT 1 COMMENT '1-启用 0-禁用',
  `is_deleted` tinyint NOT NULL DEFAULT 0,
  `created_by` varchar(64) DEFAULT NULL,
  `updated_by` varchar(64) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`),
  KEY `idx_provider` (`provider`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据源配置';

INSERT INTO `curv_data_source` (`code`,`name`,`source_type`,`provider`,`config_json`,`frequency`,`cron_expr`) VALUES
('china_bond_treasury','中债登-国债收益率','API','中债登','{"url":"http://yield.chinabond.com.cn/cbweb-mn/yieldmain","format":"json"}','daily','0 0 6 * * *'),
('china_bond_corp_aaa','中债登-企业债AAA','API','中债登','{"url":"http://yield.chinabond.com.cn/cbweb-mn/yieldmain","format":"json"}','daily','0 5 6 * * *'),
('shibor_curve','外汇交易中心-Shibor','API','外汇交易中心','{"url":"https://www.shibor.org/shibor/web/ShiborTendQuery.do","format":"json"}','daily','0 10 6 * * *'),
('repo_curve','外汇交易中心-质押式回购','API','外汇交易中心','{"url":"https://www.chinamoney.com.cn/dds/","format":"json"}','daily','0 15 6 * * *'),
('wind_ncd','Wind-同业存单','FILE','Wind','{"format":"excel","path":"/data/wind/ncd.xlsx"}','manual',NULL),
('pbc_lpr','央行-LPR','API','央行','{"url":"http://www.pbc.gov.cn/diaochatongjisi/116219/116225/index.html","format":"json"}','daily','0 30 9 * * *');

-- 2.2 采集任务定义
DROP TABLE IF EXISTS `curv_collection_task`;
CREATE TABLE `curv_collection_task` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `source_id` bigint NOT NULL,
  `task_code` varchar(64) NOT NULL,
  `task_name` varchar(128) NOT NULL,
  `schedule_type` varchar(32) NOT NULL DEFAULT 'cron' COMMENT 'cron/manual/event',
  `cron_expr` varchar(64) DEFAULT NULL,
  `params_json` json DEFAULT NULL,
  `retry_policy_json` json DEFAULT NULL COMMENT '{"max_retries":3,"backoff":"exp"}',
  `alert_threshold` int DEFAULT 3 COMMENT '失败次数超阈值告警',
  `is_enabled` tinyint NOT NULL DEFAULT 1,
  `status` tinyint NOT NULL DEFAULT 1,
  `is_deleted` tinyint NOT NULL DEFAULT 0,
  `created_by` varchar(64) DEFAULT NULL,
  `updated_by` varchar(64) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_task_code` (`task_code`),
  KEY `idx_source` (`source_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采集任务定义';

-- 2.3 采集日志
DROP TABLE IF EXISTS `curv_collection_log`;
CREATE TABLE `curv_collection_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `task_id` bigint NOT NULL,
  `source_id` bigint NOT NULL,
  `trade_date` date NOT NULL COMMENT '数据日期',
  `start_time` datetime NOT NULL,
  `end_time` datetime DEFAULT NULL,
  `duration_ms` int DEFAULT NULL,
  `status` varchar(32) NOT NULL COMMENT 'running/success/failed/timeout',
  `record_count` int DEFAULT 0,
  `error_code` varchar(64) DEFAULT NULL,
  `error_msg` text DEFAULT NULL,
  `retry_count` int NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_task_date` (`task_id`,`trade_date`),
  KEY `idx_source_date` (`source_id`,`trade_date`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采集执行日志';

-- 2.4 采集模板（文件导入）
DROP TABLE IF EXISTS `curv_collection_template`;
CREATE TABLE `curv_collection_template` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `template_code` varchar(64) NOT NULL,
  `template_name` varchar(128) NOT NULL,
  `source_id` bigint NOT NULL,
  `file_format` varchar(16) NOT NULL COMMENT 'excel/csv/xml',
  `mapping_json` json DEFAULT NULL COMMENT 'Excel列 → 内部字段映射',
  `sheet_name` varchar(64) DEFAULT NULL,
  `header_row` int NOT NULL DEFAULT 1,
  `is_enabled` tinyint NOT NULL DEFAULT 1,
  `status` tinyint NOT NULL DEFAULT 1,
  `is_deleted` tinyint NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_template_code` (`template_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文件采集模板';


-- ============================================================================
-- 第三部分：L2 数据管理层（曲线定义、利率数据、版本、血缘）
-- ============================================================================

-- 3.1 曲线定义
DROP TABLE IF EXISTS `curv_curve_definition`;
CREATE TABLE `curv_curve_definition` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(64) NOT NULL COMMENT 'cnb_treasury_yield / shibor_3m / credit_spread_aaa ...',
  `name` varchar(128) NOT NULL,
  `curve_type` varchar(32) NOT NULL DEFAULT 'base' COMMENT 'base/derived/manual',
  `category` varchar(64) DEFAULT NULL COMMENT '无风险/信用/货币市场/政策/派生',
  `currency` varchar(8) NOT NULL DEFAULT 'CNY',
  `rate_type_code` varchar(32) DEFAULT NULL COMMENT '关联 curv_rate_type_dict',
  `compound_code` varchar(32) DEFAULT NULL COMMENT '关联 curv_compound_dict',
  `day_count_code` varchar(32) DEFAULT NULL COMMENT '关联 curv_day_count_dict',
  `tenor_set_json` json DEFAULT NULL COMMENT '["1M","3M","1Y","5Y","10Y"]',
  `source_id` bigint DEFAULT NULL COMMENT '基础数据源',
  `source_mapping_json` json DEFAULT NULL COMMENT '数据源字段映射',
  `description` varchar(500) DEFAULT NULL,
  `owner_role` varchar(64) DEFAULT NULL COMMENT '资负/FTP/估值',
  `is_enabled` tinyint NOT NULL DEFAULT 1,
  `status` tinyint NOT NULL DEFAULT 1,
  `is_deleted` tinyint NOT NULL DEFAULT 0,
  `created_by` varchar(64) DEFAULT NULL,
  `updated_by` varchar(64) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`),
  KEY `idx_category` (`category`),
  KEY `idx_curve_type` (`curve_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='曲线定义';

INSERT INTO `curv_curve_definition` (`code`,`name`,`curve_type`,`category`,`currency`,`rate_type_code`,`compound_code`,`day_count_code`,`tenor_set_json`,`source_id`) VALUES
('cnb_treasury_yield','中债国债收益率','base','无风险','CNY','yield_to_maturity','compound','ACT/365','["1M","3M","6M","9M","1Y","2Y","3Y","5Y","7Y","10Y","15Y","20Y","30Y"]',1),
('cnb_policy_fin','中债国开债收益率','base','无风险','CNY','yield_to_maturity','compound','ACT/365','["1M","3M","6M","9M","1Y","2Y","3Y","5Y","7Y","10Y","15Y","20Y","30Y"]',1),
('cnb_corp_aaa','中债企业债AAA','base','信用','CNY','yield_to_maturity','compound','ACT/365','["1Y","2Y","3Y","5Y","7Y","10Y","15Y","20Y","30Y"]',2),
('cnb_corp_aa','中债企业债AA+','base','信用','CNY','yield_to_maturity','compound','ACT/365','["1Y","2Y","3Y","5Y","7Y","10Y","15Y","20Y","30Y"]',2),
('shibor_curve','Shibor','base','货币市场','CNY','spot','simple','ACT/360','["ON","1W","2W","1M","3M","6M","9M","1Y"]',3),
('repo_7d','银行间质押式回购','base','货币市场','CNY','spot','simple','ACT/360','["1D","7D","14D","1M","3M","6M","9M","1Y"]',4),
('ncd_curve','同业存单','base','货币市场','CNY','yield_to_maturity','compound','ACT/365','["1M","3M","6M","9M","1Y","2Y","3Y","5Y"]',5),
('lpr_1y','贷款市场报价利率','manual','政策','CNY','spot','simple','ACT/360','["1Y","5Y"]',6),
('credit_spread_aaa','信用利差AAA','derived','派生','CNY','par_yield','simple','ACT/365','["1Y","2Y","3Y","5Y","7Y","10Y","15Y","20Y","30Y"]',NULL),
('liquidity_spread','流动性利差','derived','派生','CNY','par_yield','simple','ACT/365','["1M","3M","6M","9M","1Y","2Y","3Y","5Y"]',NULL),
('riskfree_full','无风险收益率曲线','derived','派生','CNY','zero','continuous','ACT/365','["1D","7D","1M","3M","6M","1Y","2Y","3Y","5Y","7Y","10Y","15Y","20Y","30Y"]',NULL);

-- 3.2 利率数据（核心事实表）
DROP TABLE IF EXISTS `curv_rate_data`;
CREATE TABLE `curv_rate_data` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `curve_code` varchar(64) NOT NULL,
  `trade_date` date NOT NULL,
  `tenor` varchar(16) NOT NULL COMMENT '1D/7D/1M/3M/...',
  `rate_value` decimal(12,6) NOT NULL COMMENT '利率值（百分数原值，如 2.45 表示 2.45%）',
  `source_version` varchar(32) NOT NULL COMMENT 'raw/cleaned/official/build_xxx/derived',
  `collection_log_id` bigint DEFAULT NULL,
  `data_status` varchar(16) NOT NULL DEFAULT 'active' COMMENT 'active/revised/deleted/pending_review',
  `is_adjusted` tinyint NOT NULL DEFAULT 0 COMMENT '是否人工调整',
  `adjust_reason` varchar(500) DEFAULT NULL,
  `adjusted_by` varchar(64) DEFAULT NULL,
  `adjusted_at` datetime DEFAULT NULL,
  `data_source_code` varchar(64) DEFAULT NULL COMMENT '原始数据源编码',
  `remark` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_curve_date_tenor_ver` (`curve_code`,`trade_date`,`tenor`,`source_version`),
  KEY `idx_curve_date` (`curve_code`,`trade_date`),
  KEY `idx_date` (`trade_date`),
  KEY `idx_curve_tenor_date` (`curve_code`,`tenor`,`trade_date`),
  KEY `idx_source_version` (`source_version`),
  KEY `idx_status` (`data_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='利率数据（事实表）';

-- 3.3 曲线版本
DROP TABLE IF EXISTS `curv_curve_version`;
CREATE TABLE `curv_curve_version` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `curve_code` varchar(64) NOT NULL,
  `trade_date` date NOT NULL,
  `version_no` varchar(32) NOT NULL COMMENT 'raw/cleaned/official/build_20260817_001/...',
  `version_status` varchar(32) NOT NULL COMMENT 'raw/cleaned/official/archived',
  `parent_version_no` varchar(32) DEFAULT NULL,
  `operation_type` varchar(32) DEFAULT NULL COMMENT '采集/清洗/派生/拟合/调整/发布',
  `operation_params_json` json DEFAULT NULL,
  `operation_reason` varchar(500) DEFAULT NULL,
  `operator` varchar(64) DEFAULT NULL,
  `is_locked` tinyint NOT NULL DEFAULT 0,
  `effective_time` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_curve_date_ver` (`curve_code`,`trade_date`,`version_no`),
  KEY `idx_curve_date` (`curve_code`,`trade_date`),
  KEY `idx_status` (`version_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='曲线版本管理';

-- 3.4 派生曲线定义
DROP TABLE IF EXISTS `curv_derived_curve`;
CREATE TABLE `curv_derived_curve` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `curve_code` varchar(64) NOT NULL,
  `name` varchar(128) NOT NULL,
  `base_curve_codes_json` json NOT NULL COMMENT '["cnb_corp_aaa","cnb_treasury_yield"]',
  `formula` text NOT NULL COMMENT 'spread = cnb_corp_aaa - cnb_treasury_yield',
  `formula_type` varchar(32) DEFAULT 'simple' COMMENT 'simple/nested/script',
  `auto_update` tinyint NOT NULL DEFAULT 1,
  `description` varchar(500) DEFAULT NULL,
  `is_enabled` tinyint NOT NULL DEFAULT 1,
  `status` tinyint NOT NULL DEFAULT 1,
  `is_deleted` tinyint NOT NULL DEFAULT 0,
  `created_by` varchar(64) DEFAULT NULL,
  `updated_by` varchar(64) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_curve_code` (`curve_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='派生曲线定义';

INSERT INTO `curv_derived_curve` (`curve_code`,`name`,`base_curve_codes_json`,`formula`,`formula_type`) VALUES
('credit_spread_aaa','信用利差AAA','["cnb_corp_aaa","cnb_treasury_yield"]','cnb_corp_aaa - cnb_treasury_yield','simple'),
('liquidity_spread','流动性利差','["ncd_curve","cnb_policy_fin"]','ncd_curve - cnb_policy_fin','simple'),
('riskfree_full','无风险收益率曲线','["repo_7d","cnb_treasury_yield"]','splice(short=repo_7d, long=cnb_treasury_yield, tenor=1Y, mode=linear_transition)','script');

-- 3.5 血缘追踪
DROP TABLE IF EXISTS `curv_lineage`;
CREATE TABLE `curv_lineage` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `data_id` bigint NOT NULL COMMENT 'curv_rate_data.id',
  `data_table` varchar(64) NOT NULL DEFAULT 'curv_rate_data',
  `curve_code` varchar(64) NOT NULL,
  `trade_date` date NOT NULL,
  `tenor` varchar(16) NOT NULL,
  `source_version` varchar(32) NOT NULL,
  `upstream_sources_json` json DEFAULT NULL COMMENT '[{"step":"采集","source":"china_bond","time":"...","operator":"..."}]',
  `operations_json` json DEFAULT NULL COMMENT '[{"step":"清洗","rule":"...","time":"..."},...]',
  `reason` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_data` (`data_id`),
  KEY `idx_curve_date` (`curve_code`,`trade_date`),
  KEY `idx_version` (`source_version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='血缘链路';

-- 3.6 校验规则
DROP TABLE IF EXISTS `curv_validation_rule`;
CREATE TABLE `curv_validation_rule` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `curve_code` varchar(64) DEFAULT NULL COMMENT 'NULL 表示通用规则',
  `rule_code` varchar(64) NOT NULL,
  `rule_type` varchar(32) NOT NULL COMMENT 'not_null/range/monotonicity/reconciliation/anomaly',
  `rule_config_json` json DEFAULT NULL COMMENT '阈值等参数',
  `severity` varchar(16) NOT NULL DEFAULT 'warning' COMMENT 'info/warning/error',
  `is_enabled` tinyint NOT NULL DEFAULT 1,
  `description` varchar(500) DEFAULT NULL,
  `status` tinyint NOT NULL DEFAULT 1,
  `is_deleted` tinyint NOT NULL DEFAULT 0,
  `created_by` varchar(64) DEFAULT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rule_code` (`rule_code`),
  KEY `idx_curve` (`curve_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='校验规则配置';

INSERT INTO `curv_validation_rule` (`curve_code`,`rule_code`,`rule_type`,`rule_config_json`,`severity`) VALUES
(NULL,'rule_non_null','not_null','{}','error'),
(NULL,'rule_range','range','{"min":0,"max":20}','error'),
(NULL,'rule_monotonicity','monotonicity','{}','warning'),
(NULL,'rule_recon','reconciliation','{"threshold_bp":2}','warning'),
(NULL,'rule_anomaly','anomaly','{"neighbor_threshold_bp":30,"zscore":3}','warning');


-- ============================================================================
-- 第四部分：L3 曲线构建层（拟合参数、关键期限点）
-- ============================================================================

-- 4.1 拟合参数（时序存储）
DROP TABLE IF EXISTS `curv_fitting_param`;
CREATE TABLE `curv_fitting_param` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `curve_code` varchar(64) NOT NULL,
  `trade_date` date NOT NULL,
  `version_no` varchar(32) NOT NULL,
  `model_code` varchar(64) NOT NULL COMMENT 'nelson_siegel/svensson/...',
  `params_json` json NOT NULL COMMENT 'NS: {"beta0":2.78,"beta1":-0.85,"beta2":-1.20,"tau":1.50}',
  `rmse` decimal(12,6) DEFAULT NULL,
  `r2` decimal(12,6) DEFAULT NULL,
  `max_residual_bp` decimal(12,6) DEFAULT NULL,
  `residual_summary_json` json DEFAULT NULL,
  `fit_status` varchar(32) NOT NULL DEFAULT 'success' COMMENT 'success/failed/timeout',
  `fit_duration_ms` int DEFAULT NULL,
  `operator` varchar(64) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_curve_date_ver_model` (`curve_code`,`trade_date`,`version_no`,`model_code`),
  KEY `idx_curve_date` (`curve_code`,`trade_date`),
  KEY `idx_model` (`model_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='拟合参数（时序）';

-- 4.2 关键期限点
DROP TABLE IF EXISTS `curv_key_tenor`;
CREATE TABLE `curv_key_tenor` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `curve_code` varchar(64) NOT NULL,
  `trade_date` date NOT NULL,
  `version_no` varchar(32) NOT NULL,
  `tenor` varchar(16) NOT NULL,
  `rate_value` decimal(12,6) NOT NULL,
  `point_type` varchar(32) NOT NULL COMMENT 'anchor/inflection/peak/trough/manual',
  `remark` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_curve_date_ver_tenor` (`curve_code`,`trade_date`,`version_no`,`tenor`,`point_type`),
  KEY `idx_curve_date` (`curve_code`,`trade_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='关键期限点';


-- ============================================================================
-- 第五部分：L4 分析建模层
-- ============================================================================

-- 5.1 形态指标
DROP TABLE IF EXISTS `curv_shape_metric`;
CREATE TABLE `curv_shape_metric` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `curve_code` varchar(64) NOT NULL,
  `trade_date` date NOT NULL,
  `metric_code` varchar(64) NOT NULL COMMENT 'spread_10y_1y/spread_10y_5y/credit_spread/liquidity_spread/slope/curvature/inversion',
  `metric_name` varchar(128) NOT NULL,
  `value` decimal(20,6) NOT NULL,
  `unit` varchar(16) DEFAULT 'bp',
  `params_json` json DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_curve_date_metric` (`curve_code`,`trade_date`,`metric_code`),
  KEY `idx_metric_date` (`metric_code`,`trade_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='形态指标';

-- 5.2 情景定义
DROP TABLE IF EXISTS `curv_scenario`;
CREATE TABLE `curv_scenario` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(64) NOT NULL,
  `name` varchar(128) NOT NULL,
  `scenario_type` varchar(32) NOT NULL COMMENT 'parallel/steepener/flattener/historical/custom',
  `shock_json` json NOT NULL COMMENT '{"short_bp":-50,"long_bp":50} 或 {"vector":[...]}',
  `historical_date` date DEFAULT NULL,
  `is_preset` tinyint NOT NULL DEFAULT 0,
  `description` varchar(500) DEFAULT NULL,
  `is_enabled` tinyint NOT NULL DEFAULT 1,
  `status` tinyint NOT NULL DEFAULT 1,
  `is_deleted` tinyint NOT NULL DEFAULT 0,
  `created_by` varchar(64) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情景定义';

INSERT INTO `curv_scenario` (`code`,`name`,`scenario_type`,`shock_json`,`is_preset`) VALUES
('parallel_up_100','平行上行 100bp','parallel','{"shock_bp":100}',1),
('parallel_up_200','平行上行 200bp','parallel','{"shock_bp":200}',1),
('parallel_down_100','平行下行 100bp','parallel','{"shock_bp":-100}',1),
('steepener','陡峭化','steepener','{"short_bp":-50,"long_bp":50}',1),
('flattener','平坦化','flattener','{"short_bp":50,"long_bp":-50}',1),
('historical_2013_money_tight','2013 钱荒','historical','{"date":"2013-06-20"}',1),
('historical_2020_covid','2020 疫情','historical','{"date":"2020-04-30"}',1),
('irrbb_short_up','IRRBB 短端上行','parallel','{"shock_bp":250,"apply_to_tenors":["ON","1W","1M","3M"]}',1),
('irrbb_short_down','IRRBB 短端下行','parallel','{"shock_bp":-250,"apply_to_tenors":["ON","1W","1M","3M"]}',1);

-- 5.3 情景结果
DROP TABLE IF EXISTS `curv_scenario_result`;
CREATE TABLE `curv_scenario_result` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `scenario_id` bigint NOT NULL,
  `scenario_run_code` varchar(64) NOT NULL,
  `curve_code` varchar(64) NOT NULL,
  `trade_date` date NOT NULL,
  `asset_liability_id` varchar(64) DEFAULT NULL COMMENT '组合 ID',
  `asset_liability_name` varchar(128) DEFAULT NULL,
  `base_value` decimal(20,4) DEFAULT NULL COMMENT '组合当前价值',
  `shocked_value` decimal(20,4) DEFAULT NULL,
  `pv_change` decimal(20,4) DEFAULT NULL,
  `pv_change_pct` decimal(12,6) DEFAULT NULL,
  `nii_change` decimal(20,4) DEFAULT NULL,
  `nii_change_pct` decimal(12,6) DEFAULT NULL,
  `eve_change` decimal(20,4) DEFAULT NULL,
  `eve_change_pct` decimal(12,6) DEFAULT NULL,
  `krd_vector_json` json DEFAULT NULL COMMENT '关键利率久期向量',
  `details_json` json DEFAULT NULL,
  `run_time_ms` int DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_scenario` (`scenario_id`),
  KEY `idx_curve_date` (`curve_code`,`trade_date`),
  KEY `idx_run_code` (`scenario_run_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情景模拟结果';

-- 5.4 回溯测试
DROP TABLE IF EXISTS `curv_backtest_result`;
CREATE TABLE `curv_backtest_result` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `backtest_code` varchar(64) NOT NULL,
  `test_type` varchar(32) NOT NULL COMMENT 'fit_accuracy/predict_accuracy/strategy',
  `target_curve` varchar(64) NOT NULL,
  `model_code` varchar(64) DEFAULT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `metrics_json` json DEFAULT NULL COMMENT 'MAE/RMSE/方向准确率',
  `sample_count` int DEFAULT NULL,
  `details_json` json DEFAULT NULL,
  `conclusion` text DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_backtest_code` (`backtest_code`),
  KEY `idx_curve` (`target_curve`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回溯测试结果';

-- 5.5 智能对话历史
DROP TABLE IF EXISTS `curv_smart_dialogue`;
CREATE TABLE `curv_smart_dialogue` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `session_id` varchar(64) NOT NULL,
  `user_id` varchar(64) DEFAULT NULL,
  `role` varchar(16) NOT NULL COMMENT 'user/assistant/system',
  `query` text COMMENT '用户问题（user 角色）',
  `content` text COMMENT '助手回答（assistant 角色）',
  `agent_trace_json` json DEFAULT NULL COMMENT 'Agent 编排轨迹',
  `result_json` json DEFAULT NULL COMMENT '结构化结果（图表数据/参考资料）',
  `refs_json` json DEFAULT NULL,
  `llm_config_id` bigint DEFAULT NULL,
  `tokens_in` int DEFAULT NULL,
  `tokens_out` int DEFAULT NULL,
  `duration_ms` int DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_session_time` (`session_id`,`created_at`),
  KEY `idx_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能问数对话历史';


-- ============================================================================
-- 第六部分：L5 业务应用层（FTP/估值/监管）
-- ============================================================================

-- 6.1 FTP 加点规则
DROP TABLE IF EXISTS `curv_ftp_spread_rule`;
CREATE TABLE `curv_ftp_spread_rule` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `rule_code` varchar(64) NOT NULL,
  `product_type` varchar(32) NOT NULL COMMENT '存款/贷款/票据',
  `product_subtype` varchar(64) DEFAULT NULL,
  `tenor_min` varchar(16) DEFAULT NULL,
  `tenor_max` varchar(16) DEFAULT NULL,
  `base_curve_code` varchar(64) NOT NULL,
  `spread_bp` int NOT NULL COMMENT '加点（bp）',
  `effective_date` date NOT NULL,
  `expiry_date` date DEFAULT NULL,
  `description` varchar(500) DEFAULT NULL,
  `is_enabled` tinyint NOT NULL DEFAULT 1,
  `status` tinyint NOT NULL DEFAULT 1,
  `is_deleted` tinyint NOT NULL DEFAULT 0,
  `created_by` varchar(64) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rule_code` (`rule_code`),
  KEY `idx_product_type` (`product_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='FTP 加点规则';

-- 6.2 监管报送记录
DROP TABLE IF EXISTS `curv_regulatory_report`;
CREATE TABLE `curv_regulatory_report` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `report_code` varchar(64) NOT NULL,
  `report_name` varchar(255) NOT NULL,
  `report_type` varchar(32) NOT NULL COMMENT 'IRRBB/G33/...',
  `period` varchar(16) NOT NULL COMMENT '2026Q2/2026-08-17',
  `trade_date` date NOT NULL,
  `file_path` varchar(500) DEFAULT NULL,
  `file_format` varchar(16) DEFAULT 'xlsx',
  `status` varchar(32) NOT NULL DEFAULT 'pending' COMMENT 'pending/generated/exported/filed',
  `generated_at` datetime DEFAULT NULL,
  `exported_at` datetime DEFAULT NULL,
  `operator` varchar(64) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_report_code` (`report_code`),
  KEY `idx_period` (`period`),
  KEY `idx_trade_date` (`trade_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='监管报送记录';


-- ============================================================================
-- 第七部分：系统表（沿用 ALMD 模式，简化版）
-- ============================================================================

DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(64) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `real_name` varchar(64) DEFAULT NULL,
  `email` varchar(128) DEFAULT NULL,
  `phone` varchar(32) DEFAULT NULL,
  `org_code` varchar(64) DEFAULT NULL,
  `is_admin` tinyint NOT NULL DEFAULT 0,
  `status` tinyint NOT NULL DEFAULT 1,
  `is_deleted` tinyint NOT NULL DEFAULT 0,
  `last_login_at` datetime DEFAULT NULL,
  `created_by` bigint DEFAULT NULL,
  `updated_by` bigint DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

DROP TABLE IF EXISTS `sys_role`;
CREATE TABLE `sys_role` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `role_code` varchar(64) NOT NULL,
  `role_name` varchar(128) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `status` tinyint NOT NULL DEFAULT 1,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_code` (`role_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

INSERT INTO `sys_role` (`role_code`,`role_name`,`description`) VALUES
('admin','系统管理员','全部权限'),
('almd','资负管理岗','L4/L5 分析 + 监管报送'),
('ftp','FTP 定价岗','L3 构建 + FTP 业务'),
('risk','风险管理岗','L4 敏感度 + 压力测试'),
('data','数据治理岗','L1 采集 + L2 数据治理'),
('viewer','view','只读权限');

DROP TABLE IF EXISTS `sys_user_role`;
CREATE TABLE `sys_user_role` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `role_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_role` (`user_id`,`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联';

DROP TABLE IF EXISTS `sys_llm_config`;
CREATE TABLE `sys_llm_config` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `provider` varchar(32) NOT NULL COMMENT 'deepseek/openai/qwen/mock',
  `model` varchar(64) NOT NULL,
  `api_key` varchar(255) DEFAULT NULL,
  `api_base` varchar(255) DEFAULT NULL,
  `config_json` json DEFAULT NULL,
  `is_default` tinyint NOT NULL DEFAULT 0,
  `is_enabled` tinyint NOT NULL DEFAULT 1,
  `description` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_default` (`is_default`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LLM 配置';

INSERT INTO `sys_llm_config` (`provider`,`model`,`api_key`,`is_default`,`description`) VALUES
('deepseek','deepseek-chat','${DEEPSEEK_API_KEY}',1,'DeepSeek 默认'),
('qwen','qwen-turbo','${QWEN_API_KEY}',0,'通义千问 fallback'),
('openai','gpt-4o','${OPENAI_API_KEY}',0,'GPT-4o'),
('mock','mock-llm','mock',0,'模拟 LLM（无 token 消耗）');

DROP TABLE IF EXISTS `sys_audit_log`;
CREATE TABLE `sys_audit_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint DEFAULT NULL,
  `username` varchar(64) DEFAULT NULL,
  `module` varchar(64) DEFAULT NULL COMMENT 'L1/L2/L3/L4/L5',
  `action` varchar(64) NOT NULL COMMENT '查询/编辑/发布/删除/导出',
  `resource_type` varchar(64) DEFAULT NULL,
  `resource_id` varchar(64) DEFAULT NULL,
  `request_params` json DEFAULT NULL,
  `ip_address` varchar(64) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `duration_ms` int DEFAULT NULL,
  `result` varchar(32) DEFAULT 'success' COMMENT 'success/failed',
  `error_msg` text DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_time` (`user_id`,`created_at`),
  KEY `idx_action` (`action`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志';

-- ============================================================================
-- 收尾：初始化用户（与 ALMD/ALMT 默认账号风格一致）
-- ============================================================================
-- 默认密码 admin123（生产环境必须修改）
INSERT INTO `sys_user` (`username`,`password_hash`,`real_name`,`is_admin`) VALUES
('admin','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RqHqJFoGG','系统管理员',1);

INSERT INTO `sys_user_role` (`user_id`,`role_id`) SELECT u.id, r.id FROM sys_user u, sys_role r WHERE u.username='admin' AND r.role_code='admin';

-- ============================================================================
-- 完成
-- 数据库 curv_db 创建完毕，共 21 张表（含 4 张字典表、5 张 L1、6 张 L2、2 张 L3、5 张 L4、2 张 L5、5 张 sys）
-- ============================================================================