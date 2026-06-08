# Novel2Scenario

AI 小说转剧本工具 — 将小说文本自动转换为结构化剧本（JSON/YAML 格式），让作者快速获得可编辑、可进一步打磨的剧本初稿。

## Demo

![bandicam.mp4](assets/bandicam.mp4)

## 产品介绍

### 核心能力

上传一篇小说（TXT 文件），AI 自动完成五阶段处理，输出可直接使用的剧本：

1. **章节拆分** — 自动识别中英文章节分隔符，正则优先、LLM 后备
2. **角色提取** — 并行分析各章节，提取角色名、性格特征、角色类型，按姓名去重合并
3. **场景分析** — 识别每章内部场景边界，提取地点、时间、出场角色和节奏节拍（对话/动作/执导）
4. **剧集组织** — 将场景智能编排为电视剧集，每集含标题、摘要和场景列表
5. **剧本生成** — 组装人物表（dramatis personae）、编号场景、改编说明，支持 JSON 和 YAML 双格式导出

### 使用方式

1. 打开前端界面，输入标题/作者，拖拽或粘贴 TXT 小说文件
2. 系统自动创建 Job 并启动章节拆分
3. 每个阶段完成后，展开面板审核结果，点击「保存并继续」推进到下一阶段
4. 所有阶段完成后，可下载 JSON 或 YAML 格式的完整剧本
5. 支持多 Job 管理（左侧列表），可随时切换、删除或重新运行

### 输出效果

生成的剧本包含以下完整结构：

- **元数据**：标题、作者、总集数、原著章节数、生成时间
- **角色表**：姓名、角色定位（主角/反派/配角）、性格特征、外貌描述、关系网络
- **剧集**：每集标题、摘要、改编自原著的章节、包含的场景列表
- **场景**：编号（S01E01-01 格式）、场景标题、地点设定、出场角色、节拍序列
- **节拍**：类型化条目（对话/动作/执导），对话含说话者和台词，动作为描述
- **改编说明**：AI 对原著做了哪些调整（重组/删减/原创）

输出格式遵循 [YAML Script Schema](doc/script-yaml-schema.md) 规范，可直接导入专业剧本软件或手工进一步打磨。

## Quick Start

### Prerequisites
- Python 3.14+
- Node.js 18+
- OpenAI API key

### Setup

```bash
# Backend
pip install -e ".[dev]"
cp .env.example .env
# 编辑 .env 填入你的 API key、接口地址和模型名称

# Frontend
cd frontend
npm install
```

### 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `OPENAI_API_KEY` | 是 | - | API 密钥 |
| `OPENAI_BASE_URL` | 是 | `https://api.openai.com/v1` | API 接口地址 |
| `OPENAI_MODEL` | 是 | `gpt-4o` | 模型名称 |
| `OPENAI_AUTH_HEADER` | 否 | - | 自定义 Authorization header 值。某些国内接口不认默认的 `Bearer <key>` 格式，可设为不带前缀的 key 值 |
| `OPENAI_CUSTOM_HEADERS` | 否 | - | 完全自定义 headers（JSON 格式），如 `{"X-API-Key":"your-key"}` |
| `DATABASE_PATH` | 否 | `novel2scenario.db` | 数据库文件路径 |
| `AGENT_CONCURRENCY` | 否 | `5` | 并行 Agent 数量 |

### Run

```bash
# Terminal 1: Backend
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open http://localhost:5173

### Docker

```bash
docker compose up -d
```

Open http://localhost:3000

## Architecture

- **Backend:** FastAPI + Python 3.14
- **Frontend:** React + Vite + TypeScript
- **Storage:** SQLite
- **AI:** OpenAI GPT-4o

## Testing

```bash
pytest tests/ -v
```

## Documentation

- [YAML Script Schema](doc/script-yaml-schema.md) — 输出格式定义与设计原因
- [Design Spec](docs/superpowers/specs/2026-06-05-novel-to-script-design.md) — 系统设计文档
- [Implementation Plan](docs/plans/2026-06-05-novel-to-script.md) — 实施计划
- [Onboarding Guide](docs/ONBOARDING.md) — 新开发者入门指南
