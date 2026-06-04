# Novel2Scenario

AI 小说转剧本工具 — 将小说文本自动转换为结构化剧本（YAML 格式）。

## Quick Start

### Prerequisites
- Python 3.14+
- Node.js 20+
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

1. Chapter Splitting — 章节分割
2. Character Extraction — 角色提取（并行）
3. Scene Analysis — 场景分析（并行）
4. Episode Structuring — 剧集结构
5. Script Assembly — 剧本生成
