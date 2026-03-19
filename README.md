# Ads Data Collector V1

Ads Data Collector V1 是一个面向手游买量分析场景的广告数据采集系统。
V1 聚焦于从 TikTok Creative Center 和 Facebook Ads Library 采集结构化广告元数据，
并将结果写入 Postgres，供后续 Excel 分析、AI 分类和创意生成使用。

## 1. 项目目标

### Goal
- 采集广告列表数据
- 提取结构化字段
- 完成数据清洗与去重
- 存储到 Postgres
- 为分析层提供标准化输入

### Non-Goals
- 不抓取视频文件本体
- 不做大规模分布式爬虫
- 不实现自动投放系统

## 2. 技术栈

- Python 3.10+
- Playwright
- PostgreSQL
- PyYAML
- pytest

## 3. 核心能力

1. 广告列表采集
2. Hook / 国家 / 时间字段提取
3. 数据去重
4. 数据入库
5. 基础分析支持

## 4. 系统架构

```text
[Playwright Scraper]
        ↓
[Parser]
        ↓
[Cleaner + Deduplicator]
        ↓
[Postgres]
        ↓
[Analyzer / Excel / AI]
```

## 5. 数据模型

表名：`ads_creative`

```sql
CREATE TABLE ads_creative (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20),
    game_name VARCHAR(100),
    hook TEXT,
    creative_type VARCHAR(50),
    country VARCHAR(20),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 去重规则
- V1 默认按 `hook + platform` 去重
- 后续可扩展为 `hook + platform + country + game_name`

## 6. 模块设计

### 6.1 `scraper/`
职责：
- 打开广告库页面
- 执行滚动加载
- 获取原始 DOM 或结构化卡片数据
- 处理页面异常和重试

建议文件：
- `scraper/playwright_scraper.py`

### 6.2 `parser/`
职责：
- 从 DOM 或原始块中提取字段
- 标准化时间与国家字段
- 输出统一数据结构

建议文件：
- `parser/parser.py`

### 6.3 `storage/`
职责：
- 管理数据库连接
- 执行插入与更新
- 实现去重逻辑
- 记录入库日志

建议文件：
- `storage/db.py`

### 6.4 `analyzer/`
职责：
- 对 Hook 做规则分类或 AI 分类
- 基于首末出现时间标记潜在爆款

建议文件：
- `analyzer/hook_classifier.py`

## 7. 推荐目录结构

```text
ads_collector/
├── scraper/
│   └── playwright_scraper.py
├── parser/
│   └── parser.py
├── storage/
│   └── db.py
├── analyzer/
│   └── hook_classifier.py
├── config/
│   └── config.yaml
├── tests/
│   └── test_scraper.py
├── main.py
├── README.md
└── AGENTS.md
```

## 8. 数据流

1. 启动采集任务
2. 选择平台和关键词或游戏名
3. 打开广告库页面
4. 执行滚动加载
5. 抓取页面节点
6. 解析结构化字段
7. 清洗和去重
8. 写入 Postgres
9. 输出分析数据

## 9. 配置设计

推荐配置文件：`config/config.yaml`

```yaml
platforms:
  - tiktok
  - facebook

scrape:
  max_scroll: 10
  delay: 2

database:
  type: postgres
  host: localhost
  port: 5432
  name: ads_collector
  user: postgres
  password: postgres
```

说明：
- `delay` 建议统一使用秒级数字，避免后续解析 `2s` 字符串
- 敏感配置在正式环境建议改为环境变量注入

## 10. 开发规范

### 10.1 编码要求
- 使用 Python 3.10+
- 代码模块化，禁止把所有逻辑堆在 `main.py`
- 每个模块必须可单独测试
- 异常必须写日志
- 优先保证数据完整性

### 10.2 日志规范
- 采集开始、结束、失败必须记录
- 页面解析异常必须记录原始上下文
- 数据库写入失败必须记录错误信息
- 去重命中数量建议单独统计

### 10.3 去重规范
- 不允许重复写入相同广告
- 插入前先查重，或使用数据库唯一索引
- 建议后续增加唯一约束：

```sql
CREATE UNIQUE INDEX uniq_ads_hook_platform
ON ads_creative(platform, hook);
```

## 11. 测试规范

### 11.1 功能测试
- 至少抓取到 10 条数据
- `platform`、`hook`、`country` 等关键字段不为空

### 11.2 稳定性测试
- 连续运行 30 分钟
- 成功率不低于 80%

### 11.3 数据质量测试
- Hook 文案可读
- 无乱码
- 国家字段正确
- 时间字段可解析

### 11.4 业务验证
- 基于采集数据生成 3 条广告创意
- 用于后续 CTR 测试验证

## 12. 开发阶段拆分

### Phase 1: 基础框架
- 初始化项目结构
- 配置文件与日志系统
- Postgres 连接层

### Phase 2: TikTok 采集
- 实现 Playwright 基础采集器
- 完成 TikTok DOM 解析
- 打通入库流程

### Phase 3: Facebook 采集
- 实现 Facebook Ads Library 采集
- 适配解析规则
- 打通统一数据模型

### Phase 4: 分析与输出
- Hook 分类
- 爆款标记
- 导出 Excel 或 CSV

## 13. 任务拆解建议

### P0
- 建立项目目录
- 初始化配置与日志
- 实现数据库建表和连接

### P1
- 完成 TikTok Scraper
- 完成 Parser
- 完成去重入库

### P2
- 完成 Facebook Scraper
- 增加测试样例
- 增加基础分析逻辑

### P3
- 增加导出能力
- 增加规则分类器
- 增加任务调度与重试

## 14. 运行流程建议

### 本地开发
1. 安装 Python 依赖
2. 安装 Playwright 浏览器
3. 启动 Postgres
4. 初始化数据库表
5. 运行 `main.py`
6. 运行测试

### 推荐命令

```bash
pip install -r requirements.txt
playwright install
pytest
python main.py
```

## 15. 风险与注意事项

- 广告库页面结构可能变化，Parser 要保留容错
- 平台存在反爬限制，Scraper 需控制频率
- 时间字段格式可能因地区变化
- 国家字段可能是缩写或多语言，需要标准化
- 去重规则过于简单时，可能误伤相似广告

## 16. V1 完成标准

满足以下条件即可认为 V1 可交付：
- 至少支持 TikTok 和 Facebook 两个平台
- 单次任务可稳定采集并入库
- 关键字段解析成功
- 数据可去重
- 基础测试通过
- 可输出给 Excel 或 AI 使用

## 17. 下一步建议

1. 先创建项目骨架和 `requirements.txt`
2. 优先实现 TikTok 采集链路
3. 再补 Facebook 适配
4. 最后加入分析与导出能力

