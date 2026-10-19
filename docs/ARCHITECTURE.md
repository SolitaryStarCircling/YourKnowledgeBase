# ARCHITECTURE.md — 个人 AI 知识库架构说明

## 1. 目标与约束

- 目标：本地优先的个人 AI 知识库——导入文档、语义搜索、RAG 问答（带来源引用），同时作为学习清晰分层架构的范本项目。
- 约束：预算 0 元（固定成本为 0，API 调用按量付费可接受）；隐私优先；BYOK 不绑定厂商；不引入重型框架（框架只当零件用）；交付标准为"简历级"——能用 + 文档完整 + 有测试。
- 运行形态：本地 + 局域网起步（后端在 PC，手机装 APK 连局域网），预留上服务器的可部署性。

## 2. 技术栈

| 位置 | 选型 | 说明 |
|---|---|---|
| 后端框架 | FastAPI | 轻量、类型友好 |
| RAG 编排 | 自写 | 不用 LangChain 等重型框架 |
| 向量库 | LanceDB | 嵌入式、零服务、文件即库 |
| 元数据 | SQLite | 文档/板块/索引状态 |
| 前端 | Flutter | 安卓 APK + 桌面 + Web 一套代码（iOS 不做） |
| LLM / 嵌入 | 云端 API（BYOK） | 经 Provider 端口抽象，预留本地模型（Ollama）适配器 |
| 测试 | pytest / flutter test | Mock 端口测用例，不调真实 API |
| 部署 | 本地 + 局域网，Docker Compose 预留 | 可平移到服务器 |

## 3. 数据流

### 3.1 离线索引流水线

```
导入(md/txt/PDF/URL) → 解析 → 分块 → 嵌入【出网】 → 存储(LanceDB + SQLite)
```

- 每个文档走完全相同的五步。
- **增量更新**：按文档内容哈希判断，内容变了才重新解析/嵌入；删除按 `doc_id` 清理向量与元数据。
- 出网的只有"嵌入"一步（调用用户配置的 Embedding API）。

### 3.2 在线问答流水线

```
提问 → 检索(查询向量化【出网】 + Top-K 召回【本地】) → RAG 生成【出网】 → 回答 + 引用
```

- 检索在本地 LanceDB 上做 Top-K 向量召回。
- RAG 生成把检索片段拼进提示词调用 LLM。
- **引用约束**：回答中的引用只能来自检索到的真实片段（chunk_id / 文档名 / 原文摘录），不允许模型编造来源。

### 3.3 出网边界（隐私保证）

全系统只有两处出网，且都发生在 `infra/providers/`：
1. 文档/查询的**向量化**（Embedding API）
2. **RAG 生成**（LLM API）

其余解析、分块、存储、检索全部在本机完成。

## 4. 分层架构

| 层 | 目录 | 职责 | 允许依赖 |
|---|---|---|---|
| 入口层 | `api/` `cli/` | 参数校验、DTO ↔ 领域对象转换、调用用例 | 仅应用层 |
| 应用层 | `usecases/` | 编排一个完整用例（导入/搜索/问答/板块管理），事务边界 | 领域层（实体 + 端口） |
| 领域层 | `core/` | 实体、端口抽象、业务规则（分块规则、引用格式、增量判定） | 无（纯 Python） |
| 基础设施层 | `infra/` | 实现端口：LanceDB、SQLite、解析器、Provider API 适配器 | 领域层的端口定义 |

依赖铁律：

1. 依赖只指向内层：`api → usecases → core`，`infra → core`；反向 import 禁止。
2. `core/` 零框架依赖。
3. 端口在 `core/ports` 定义，在 `infra/` 实现；组装发生在组装根 `app/bootstrap.py`（CLI 与 API 共用，换厂商/换存储只改这里）。

## 5. 目录结构

```text
YourKnowledgeBase/
├── AGENTS.md                     # AI 协作者约束（根目录，供工具自动读取）
├── backend/
│   ├── app/
│   │   ├── api/                  # 入口层：FastAPI（app.py 错误映射 / schemas.py / deps.py / routes/）
│   │   ├── cli/                  # 入口层：Typer 命令行
│   │   ├── core/                 # 领域层：entities/ ports/ services/（纯 Python）
│   │   ├── usecases/             # 应用层：一用例一文件
│   │   ├── infra/                # 基础设施层：parsers/ chunking/ vectordb/ db/ providers/
│   │   ├── bootstrap.py          # 组装根：拼装端口实现与 Provider 工厂（CLI/API 共用）
│   │   └── config.py
│   ├── tests/                    # unit/ integration/
│   ├── data/                     # 本地数据（git 忽略）
│   ├── pyproject.toml
│   └── docker-compose.yml
├── frontend/                     # Flutter 三端客户端（安卓 APK / Windows / Web）
│   ├── lib/
│   │   ├── app/                  # 应用壳（导航）+ 依赖注入（AppScope）
│   │   ├── shared/               # api/ state/ widgets/（API 客户端、模型、会话设置、共用组件）
│   │   └── features/             # import/ search/ ask/ sections/ settings/（一页面一文件）
│   └── test/                     # 模型 / API 客户端 / 页面测试（MockClient 假后端）
└── docs/
    └── ARCHITECTURE.md           # 本文件
```

## 6. 核心端口（`core/ports/`）

| 端口 | 职责 | 实现位置 |
|---|---|---|
| `Parser` | 字节流/URL → 结构化文本 | `infra/parsers/` |
| `Chunker` | 文本 → 有序分块（含定位信息） | `infra/chunking/`（规则在 `core/services/`） |
| `EmbeddingProvider` | 文本列表 → 向量列表 | `infra/providers/`（API / 预留 Ollama） |
| `LLMProvider` | 提示词 → 回答文本 | `infra/providers/` |
| `VectorStore` | 向量的增/删/Top-K 检索（按 doc_id） | `infra/vectordb/`（LanceDB） |
| `DocumentRepository` | 文档元数据 CRUD、按板块取文档/清归属 | `infra/db/`（SQLite） |
| `SectionRepository` | 板块元数据 CRUD（名称唯一） | `infra/db/`（SQLite） |
| `LocalConfigStore` | 本地 `.env` 配置读写（Key 类条目由用例层禁写） | `infra/secrets/` |

## 7. 领域模型（`core/entities/`）

- `Document`：id、标题、来源类型（file/url）、来源地址、内容哈希、所属板块、导入时间
- `Chunk`：id、所属文档、序号、文本、（向量由 VectorStore 管理）
- `Section`（板块）：id、名称、描述——用户自建的数据分区
- `Citation`：chunk_id、doc_id、原文摘录、相关度得分——问答引用的载体

## 8. HTTP 接口（`api/`）

组装根 `app/bootstrap.py` 提供 `ServiceContainer`（解析器/分块器/存储端口 + Embedder/LLM 工厂）；`create_app(container)` 拼装 FastAPI，测试可注入内存假件。

| 方法 | 路径 | 用例 | 说明 |
|---|---|---|---|
| GET | `/health` | — | 存活检查，零 Key 依赖 |
| POST | `/documents/import` | `import_document` | 导入 md/txt/PDF/URL，返回 `status/doc_id/title/chunk_count` |
| POST | `/search` | `semantic_search` | 语义搜索，返回命中片段 + 来源 |
| POST | `/ask` | `answer_question` | RAG 问答，返回回答 + 引用（只来自真实检索片段） |
| POST | `/sections` | `create_section` | 建板块（201） |
| GET | `/sections` | `list_sections` | 板块列表 |
| PATCH | `/sections/{name}` | `update_section` | 重命名/改描述 |
| DELETE | `/sections/{name}` | `delete_section` | 删板块（204，无 body） |
| GET | `/config` | `show_config_status` | 配置状态（Key 一律脱敏展示） |
| PUT | `/config/{name}` | `configure_provider` | 写非密配置（写 `*_API_KEY` 拒绝，程序绝不代写 Key） |
| DELETE | `/config/{name}` | `clear_config_value` | 清除配置（204） |

约定：

- **BYOK 会话模式**：请求头 `X-Embedding-Api-Key` / `X-Llm-Api-Key` 只进本请求内存，优先级高于环境变量，不落任何文件。
- **CORS**：放行任意来源（`CORSMiddleware`），供 Web 端浏览器跨域调用；应用无 Cookie/鉴权，默认只在本机与局域网可达。
- **错误映射**：`ValueError`/`FileNotFoundError` → 400；缺 Key 等 `RuntimeError` → 503；请求校验失败 → 422（响应剥掉 `input`/`ctx`，防止密钥回显）；其余异常 → 500 固定文案。
- **惰性构造**：Embedder/LLM 按请求构造，导入/搜索/问答互不绑架；`/health`、板块、配置接口零 Key 依赖。
- 启动：`cd backend && uvicorn app.api.main:app --host 0.0.0.0 --port 8000`（局域网访问把 `localhost` 换成 PC 局域网 IP）。

## 9. Flutter 前端（`frontend/`）

三端一套代码：安卓 APK + 桌面（Windows）+ Web，不做 iOS。只引轻量 `http`，不带重型状态框架。

分层（依赖单向：`features → shared`，`app` 做组装）：

- `lib/app/`：应用壳 `home_shell.dart`（窄屏底部导航 / 宽屏侧边导航，IndexedStack 保状态）+ 依赖注入 `app_scope.dart`（InheritedWidget 挂 `AppSettings` + `ApiClient`）
- `lib/shared/`：`api/api_client.dart`（全部 HTTP 调用、BYOK 会话头、错误映射）、`api/api_models.dart`（对齐后端 `schemas.py`）、`state/app_settings.dart`（后端地址 + 会话密钥，只存内存）、`widgets/section_picker.dart`（板块下拉共用组件）
- `lib/features/<功能>/`：import / search / ask / sections / settings 五页，一页面一文件（对话框等独立组件单独成文件），单文件 ≤300 行

关键约定：

- **会话密钥**：输入框只写 `AppSettings`（内存），随请求头发送，应用退出即失效；配置展示一律用后端脱敏值，前端绝不回传。
- **错误展示**：`ApiException` 取后端 `detail` 文案，网络层失败给通用提示，不暴露原始报文。
- **测试**：`flutter test` 全走 `http` 的 MockClient 假后端，零 API 花费。
- 运行：`cd frontend && flutter run -d windows`（桌面）/ `-d chrome`（Web）/ 连真机 `-d <device>`；打包 APK：`flutter build apk`。

## 10. 部署形态

1. **纯本地**：后端 uvicorn 起在 localhost，前端 `flutter run`（桌面/Web）。
2. **局域网**：后端监听 `0.0.0.0:8000`，手机 APK 配 PC 的局域网 IP 即可访问。
3. **服务器（预留）**：`docker-compose.yml` 打包后端；数据层是端口，向量库可平滑换 Qdrant 等可部署方案，`core/` 不动。

## 11. 范围边界

- v1：导入（md/txt/PDF/URL）、分块、嵌入、语义搜索、RAG 问答（带引用）、板块管理、增量更新、BYOK 设置（会话/持久多模式）。
- v2：标签/分类、Word/EPUB、OCR、浏览器插件、多知识库切换、iOS。
