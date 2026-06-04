# Novel2Scenario

AI 小说转剧本工具 — 将小说文本自动转换为结构化剧本（JSON/YAML 格式）。

## Quick Start

### Prerequisites
- Python 3.14+
- Node.js 18+
- OpenAI API key

### Setup

```bash
# Backend
pip install -e ".[dev]"
echo "OPENAI_API_KEY=sk-..." > .env

# Frontend
cd frontend
npm install
```

### Run

```bash
# Terminal 1: Backend
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open http://localhost:5173

## Architecture

- **Backend:** FastAPI + Python 3.14
- **Frontend:** React + Vite + TypeScript
- **Storage:** SQLite
- **AI:** OpenAI GPT-4o

## Pipeline

1. **Chapter Splitting** — 章节分割（正则检测章节分隔符，LLM 后备）
2. **Character Extraction** — 角色提取（并行处理各章节，去重合并）
3. **Scene Analysis** — 场景分析（识别场景边界、节拍、台词、动作、执导）
4. **Episode Structuring** — 剧集结构（将场景组织为有意义的剧集）
5. **Script Assembly** — 剧本生成（生成结构化剧本 + 改编说明）

## Testing

```bash
pytest tests/ -v
```

## Documentation

- [YAML Script Schema](doc/script-yaml-schema.md) — 输出格式定义与设计原因
- [Design Spec](docs/superpowers/specs/2026-06-05-novel-to-script-design.md) — 系统设计文档
- [Implementation Plan](docs/plans/2026-06-05-novel-to-script.md) — 实施计划
