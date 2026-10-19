# YourKnowledgeBase · 个人 AI 知识库

> 本地优先的"赛博图书馆"：导入 Markdown / txt / PDF / 网页，
> 语义搜索 + RAG 问答（附真实来源引用）。
> BYOK（Bring Your Own Key）自填大模型 API Key，不绑定厂商；数据与密钥只存本地。
>
> **PS：此项目暂无后续开发计划（失去需求），保留 GitHub 仓库仅做想法备案，后续可能恢复更新也可能以其他项目形式重建。**

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=fff)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=fff)
![Flutter](https://img.shields.io/badge/Flutter-02569B?logo=flutter&logoColor=fff)
![LanceDB](https://img.shields.io/badge/LanceDB-embedded-8A678A)

![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20Windows%20%7C%20Web-8A678A)

**发布：[v0.1.0 →](https://github.com/SolitaryStarCircling/YourKnowledgeBase/releases/latest)** 源码包 · 含版本变更说明

---

YourKnowledgeBase 是一款<strong>本地优先（local-first）</strong>的个人 AI 知识库。它把「数据与密钥的归属权」当作首要约束：文档、向量、元数据全部落在本机 `data/` 目录，API Key 由使用者自填、只存本地，全系统仅向量化与 RAG 生成两处出网，且只指向使用者自己配置的接口。无账号体系、无云同步、无遥测。

RAG 编排为自写实现，刻意不引入 LangChain 等重型框架；回答携带的引用只来自检索到的片段（chunk_id / 文档名 / 原文摘录），不编造来源。依赖方向严格单向：`api → usecases → core`，`infra → core`；`core/` 保持纯 Python、零框架依赖，更换模型厂商只需在 `infra/providers/` 新增适配器。

---

## 功能

**导入与索引**

- 多格式导入：Markdown / txt / PDF / 网页 URL
- 解析 → 分块 → 嵌入 → 存储（LanceDB + SQLite）完整离线索引链路
- 增量更新：按内容哈希判定，内容未变不重复嵌入

**检索与问答**

- 语义搜索：查询向量化 + Top-K 向量召回，返回命中片段
- RAG 问答：回答附带真实引用（chunk_id / 文档名 / 原文摘录），引用只来自检索片段

**知识管理**

- 板块（Section）管理：知识自建分区，按板块导入与检索
- 文档列表、内容查看、重命名、删除

**BYOK 与凭据**

- 多模式存 Key：会话模式（仅存内存，进程退出即失效）/ 环境变量 / `.env` 文件
- Key 不进 git、不进日志、不进数据库，配置接口一律脱敏回显

**客户端与入口**

- Flutter 三端客户端：Android APK / Windows 桌面 / Web，一套代码
- 双入口：FastAPI HTTP API + Typer 命令行

---

## 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| 后端 | Python 3.11+ / FastAPI | 自写 RAG 编排，不引入 LangChain 等重型框架 |
| 向量库 | LanceDB | 嵌入式、零服务、文件即库 |
| 元数据 | SQLite | 文档 / 板块元数据 |
| 前端 | Flutter | Android / Windows / Web 三端一套代码 |
| LLM 与嵌入 | 云端 API（BYOK，OpenAI 兼容） | 预留本地 Provider 接口（如 Ollama），默认不启用 |
| 命令行 | Typer | 导入 / 检索 / 问答 / 板块 / 配置子命令 |

---

## 架构与数据流

依赖只指向内层：`api → usecases → core`，`infra → core`；`core/` 零框架依赖；
端口在 `core/ports` 定义抽象，实现在 `infra/`——更换模型厂商只需新增 Provider 适配器，更换向量库只需新增 VectorStore 实现，`core/` 与 `usecases/` 不动。

```text
backend/app/
├── api/        # 入口层：FastAPI（校验、DTO、调用用例）
├── cli/        # 入口层：Typer 命令行
├── usecases/   # 应用层：一用例一文件（导入/搜索/问答/板块/配置）
├── core/       # 领域层：实体 + 端口 + 业务规则（纯 Python，零框架依赖）
└── infra/      # 基础设施层：解析器 / 分块 / LanceDB / SQLite / Provider 适配器
```

```text
离线索引：导入 → 解析 → 分块 → 嵌入 → 存储（LanceDB + SQLite）
在线问答：提问 → 检索（查询向量化 + Top-K 召回） → RAG 生成 → 回答 + 引用
```

详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

---

## 隐私与凭据模型

- **出网边界**：全系统仅两处出网——向量化与 RAG 生成，且只指向使用者自己配置的 API；网络请求只允许出现在 `infra/providers/`
- **Key 三级读取**：运行时输入（会话模式）> 环境变量 > `.env` 文件；缺失时友好提示，不崩溃、不回显内容
- **会话模式**：请求头 `X-Embedding-Api-Key` / `X-Llm-Api-Key` 只进本请求内存，进程退出即失效，不落任何文件
- **Key 不落盘明文**：不进 git、不进日志、不进数据库、不出现在异常信息与 API 响应中
- **数据只落本地**：文档、向量、元数据全部在 `data/`；无任何遥测 / 统计 SDK
- **日志约束**：文档正文不进日志，只允许 `doc_id` / 内容哈希 / 长度

---

## 工程质量

- 后端 `pytest` **158 项全绿**：`core/` 业务规则（分块、引用格式、增量判定）全覆盖；`usecases/` 测试一律 Mock 端口，不触发真实 API；integration 测试用临时目录并在结束清理
- `ruff check` 通过（lint + format，单一配置源 `pyproject.toml`）
- 前端 `flutter test` 使用 MockClient 假后端，零 API 花费

---

## 环境准备

1. **Python 3.11+** —— <https://www.python.org>
2. **Flutter SDK** —— 仅构建客户端时需要，<https://docs.flutter.dev/get-started/install>
3. **API Key** —— 任一 OpenAI 兼容接口（嵌入 + 问答可分开配置）

## 快速开始

### 后端服务

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env    # 填入自己的 API Key
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

### Flutter 客户端

```bash
cd frontend
flutter pub get
flutter run -d windows     # 桌面；或 -d chrome 网页版
flutter build apk          # 打包 Android APK
```

### 命令行入口

```bash
cd backend
python -m app.cli.main import-note <文件路径或URL> --section <板块名>
python -m app.cli.main search "你的查询"
python -m app.cli.main ask "你的问题"
python -m app.cli.main section list
```

完整操作说明见 [docs/使用手册.md](docs/使用手册.md)。

---

## API 速览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 存活检查（零 Key 依赖） |
| POST | `/documents/import` | 导入 md/txt/PDF/URL |
| GET | `/documents` | 文档列表 / 内容 / 重命名 / 删除 |
| POST | `/search` | 语义搜索 |
| POST | `/ask` | RAG 问答（回答 + 引用） |
| POST/GET/PATCH/DELETE | `/sections` | 板块管理 |
| GET/PUT/DELETE | `/config` | 配置查看与设置（Key 一律脱敏） |

## 配置（BYOK）

```text
EMBEDDING_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL   # 嵌入接口
LLM_API_KEY / LLM_BASE_URL / LLM_MODEL                     # 问答接口
```

读取优先级：**运行时输入（会话模式）> 环境变量 > `.env` 文件**。

---

## 项目结构

```text
YourKnowledgeBase/
├── backend/
│   ├── app/
│   │   ├── api/          FastAPI 入口（路由、DTO、依赖注入）
│   │   ├── cli/          Typer 命令行入口
│   │   ├── usecases/     用例编排（一用例一文件）
│   │   ├── core/         领域层：实体 + 端口 + 业务规则
│   │   └── infra/        解析器 / 分块 / LanceDB / SQLite / Provider 适配器
│   ├── tests/            pytest（Mock 端口 + 临时目录集成测试）
│   └── pyproject.toml
├── frontend/             Flutter 三端客户端（features/ 分模块）
├── docs/                 ARCHITECTURE / API / 使用手册
└── data/                 本地数据（向量库 + 元数据，不入库）
```

## 数据存放位置

文档、向量库、元数据均由 `backend/data/` 承载，**不在本仓库内**：
克隆仓库不会带上任何真实知识数据，备份直接拷贝 `data/` 目录即可。

---

## 开发者

[SolitaryStarCircling](https://github.com/SolitaryStarCircling) · 个人独立开发
