# AGENTS.md — AI 协作者约束文件

> 本文件是给 AI 编码代理 / 协作者的**硬约束**。修改任何代码前必须先读完。
> 与一般偏好冲突时：架构规则与安全红线 > 代码规范 > 其他建议。

## 项目是什么

个人 AI 知识库（本地优先的"赛博图书馆"）：
导入 Markdown / txt / PDF / 网页 URL → 解析 → 分块 → 嵌入 → 存本地向量库 → 语义搜索 → RAG 问答（带来源引用）。
BYOK：用户自填大模型 API Key，不绑定厂商，Key 只存本地。

## 技术栈（不得擅自更换或引入重型框架）

- 后端：Python 3.11+ / FastAPI / **自写 RAG 编排**
- 存储：LanceDB（向量）+ SQLite（元数据）
- 前端：Flutter（安卓 APK + 桌面 + Web；**iOS 不做**）
- LLM 与嵌入：云端 API（BYOK），预留本地 Provider 接口（如 Ollama），默认不启用
- 测试：pytest（后端）、flutter test（前端）
- 工具：ruff（lint + format）、flutter_lints、dart format
- 部署：本地 + 局域网起步，Docker Compose 预留

## 硬性架构规则（违反即视为错误）

1. **依赖只指向内层**：`api → usecases → core`，`infra → core`。禁止任何反向 import。
2. **`core/` 零框架依赖**：禁止 import `fastapi` / `pydantic` / `lancedb` / `sqlite3` / `requests` / `httpx` 等；只允许纯 Python 标准库。
3. **端口在 `core/ports` 定义（抽象），实现放 `infra/`**。换模型厂商 = 新增 Provider 适配器；换向量库 = 新增 VectorStore 实现；`core/` 与 `usecases/` 不动。
4. **一个用例一个文件**：`usecases/<动词_名词>.py`，函数名即用例名。
5. **出网白名单**：网络请求只允许出现在 `infra/providers/`。其他层出网即违规。

## 代码规范

**Python（后端）**
- `ruff` 负责 lint + format，配置写在 `pyproject.toml`，单一配置源。
- `core/` 与 `usecases/` 的公共函数必须有完整类型标注；`infra/` 尽量标注。
- 命名：模块/函数 `snake_case`，类 `PascalCase`，常量 `UPPER_CASE`；端口按用途命名（`EmbeddingProvider`、`VectorStore`、`DocumentRepository`）。
- 一个函数只做一件事（约 ≤40 行）；注释只写"为什么"，不写"做了什么"；端口必须有 docstring。

**Dart（前端）**
- 官方 `flutter_lints` + `dart format`，不自定义风格。
- 按 `features/` 分目录，一个页面/组件一个文件；单文件约 ≤300 行，超出就拆。

## 提交规范（Conventional Commits）

- 格式：`type(scope): description`，例：`feat(usecases): add semantic search use case`
- type：`feat | fix | docs | refactor | test | chore | perf | build`
- scope：`core | usecases | api | cli | infra | frontend | docs`
- 描述用英文、动词开头、说清动机；**一次提交只做一件事**，可独立回滚。
- 提交前必须 `ruff check .` + `pytest` 全绿（前端改动需 `flutter test` 全绿）。

## 测试要求

- `core/` 业务规则（分块、引用格式、增量判定）**必须有测试**。
- `usecases/` 测试一律使用 Mock 端口，**禁止真实调用外部 API**（不花 API 钱）。
- integration 测试可用真实 LanceDB / SQLite，但必须写入临时目录并在测试后清理。
- `core/` 覆盖率目标 ≥80%；不为凑覆盖率写无意义测试；不测第三方库本身。

## 安全 / 隐私红线（最高优先级，任何情况下不得违反）

- API Key：**不进 git、不进日志、不出现在异常信息与 API 响应中**；"仅本次会话"模式只存内存，进程退出即失效。
- 文档正文不打印进日志（只允许 `doc_id` / 内容哈希 / 长度）。
- 不引入任何遥测 / 统计 SDK；数据文件只落本地 `data/`。
- `.env` 必须在 `.gitignore` 中；仓库里只允许出现无值的 `.env.example`。

## 密钥配置约定

- 统一命名（不绑定厂商）：`LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`，`EMBEDDING_API_KEY` / `EMBEDDING_BASE_URL` / `EMBEDDING_MODEL`。
- 读取优先级：**运行时输入（会话模式）> 环境变量 > `.env` 文件**。
- 启动时校验 Key：缺失给出友好提示，不崩溃、不回显 Key 内容；Key 永不写入数据库或任何配置文件明文。

## v1 范围（不要越界实现）

- v1 做：导入（md / txt / PDF / URL）→ 分块 → 嵌入 → 语义搜索；RAG 问答（带引用）；板块（Section）管理；增量更新（按内容哈希）；BYOK 设置（多模式存 Key）。
- v2 不做：标签 / 分类、Word / EPUB、OCR、浏览器插件、多知识库切换、iOS。

## 目录速查

- `backend/app/core/` 领域层（实体 + 端口 + 业务规则，纯 Python）
- `backend/app/usecases/` 应用层（用例编排）
- `backend/app/api/`、`backend/app/cli/` 入口层
- `backend/app/infra/` 基础设施层（LanceDB / SQLite / 解析器 / Provider 适配器）
- `frontend/lib/features/` 前端功能模块
- 详细架构见 `docs/ARCHITECTURE.md`
