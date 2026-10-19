"""CLI 入口层：命令定义。

依赖的具体拼装在 app.bootstrap（组装根，与 API 共用）；
命令只做参数解析与结果展示，业务逻辑全部在用例层。
"""

import os

import typer

from app.bootstrap import ENV_FILE, build_config_store, build_llm, build_repos, build_services
from app.usecases.answer_question import answer_question
from app.usecases.clear_provider_config import clear_provider_config
from app.usecases.configure_provider import configure_provider
from app.usecases.create_section import create_section
from app.usecases.delete_section import delete_section
from app.usecases.import_document import import_document
from app.usecases.list_sections import list_sections
from app.usecases.semantic_search import semantic_search
from app.usecases.show_config_status import show_config_status
from app.usecases.update_section import update_section

cli = typer.Typer(help="个人 AI 知识库 CLI（导入 md/txt/PDF/URL -> 语义搜索 -> RAG 问答）")
section_app = typer.Typer(help="板块管理：创建 / 查看 / 修改 / 删除数据分区")
config_app = typer.Typer(help="BYOK 配置：密钥与模型设置（Key 只存本地，绝不进 git）")
cli.add_typer(section_app, name="section")
cli.add_typer(config_app, name="config")


@cli.command("import-note")
def import_note(
    source: str,
    section: str = typer.Option(None, "--section", help="所属板块名称"),
    embedding_api_key: str = typer.Option(
        None, "--embedding-api-key", help="会话模式密钥：仅本次使用，不落盘"
    ),
):
    """导入一篇笔记或网页：支持本地 md/txt/PDF 文件路径，或 http(s) 网页 URL。"""
    session = {"EMBEDDING_API_KEY": embedding_api_key} if embedding_api_key else None
    parser, chunker, embedder, vector_store, doc_repo, section_repo = build_services(session)
    try:
        result = import_document(
            source,
            parser=parser,
            chunker=chunker,
            embedder=embedder,
            vector_store=vector_store,
            doc_repo=doc_repo,
            section_repo=section_repo,
            section=section,
        )
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        typer.echo(f"[失败] {exc}")
        raise typer.Exit(code=1) from None

    verb = {"created": "已导入", "updated": "已更新", "skipped": "内容未变化，跳过"}[result.status]
    typer.echo(f"[{verb}] 《{result.title}》 doc_id={result.doc_id} 分块数={result.chunk_count}")


@cli.command("search")
def search(
    query: str,
    top_k: int = typer.Option(5, "--top-k", help="返回条数"),
    section: str = typer.Option(None, "--section", help="限定板块名称"),
    embedding_api_key: str = typer.Option(
        None, "--embedding-api-key", help="会话模式密钥：仅本次使用，不落盘"
    ),
) -> None:
    """语义搜索：返回相关片段 + 来源。"""
    session = {"EMBEDDING_API_KEY": embedding_api_key} if embedding_api_key else None
    _, _, embedder, vector_store, doc_repo, section_repo = build_services(session)
    try:
        hits = semantic_search(
            query,
            embedder=embedder,
            vector_store=vector_store,
            top_k=top_k,
            section=section,
            section_repo=section_repo,
            doc_repo=doc_repo,
        )
    except (ValueError, RuntimeError) as exc:
        typer.echo(f"[失败] {exc}")
        raise typer.Exit(code=1) from None

    if not hits:
        typer.echo("没有找到相关内容（知识库为空？先用 import-note 导入笔记）")
        return

    for rank, hit in enumerate(hits, start=1):
        header = (
            f"{rank}. [得分 {hit.score:.3f}] 《{hit.title}》 来源: {hit.source} (片段 #{hit.index})"
        )
        typer.echo(header)
        typer.echo(f"   {hit.text[:120]}...")


@cli.command("ask")
def ask(
    question: str,
    top_k: int = typer.Option(5, "--top-k", help="检索片段数"),
    section: str = typer.Option(None, "--section", help="限定板块名称"),
    embedding_api_key: str = typer.Option(
        None, "--embedding-api-key", help="会话模式密钥：仅本次使用，不落盘"
    ),
    llm_api_key: str = typer.Option(None, "--llm-api-key", help="会话模式密钥：仅本次使用，不落盘"),
) -> None:
    """RAG 问答：基于知识库回答问题，引用只来自真实检索片段。"""
    session = {
        name: value
        for name, value in (
            ("EMBEDDING_API_KEY", embedding_api_key),
            ("LLM_API_KEY", llm_api_key),
        )
        if value
    }
    _, _, embedder, vector_store, doc_repo, section_repo = build_services(session or None)
    llm = build_llm(session or None)
    try:
        answer = answer_question(
            question,
            llm=llm,
            embedder=embedder,
            vector_store=vector_store,
            top_k=top_k,
            section=section,
            section_repo=section_repo,
            doc_repo=doc_repo,
        )
    except (ValueError, RuntimeError) as exc:
        typer.echo(f"[失败] {exc}")
        raise typer.Exit(code=1) from None

    typer.echo(answer.text)
    if not answer.citations:
        return

    typer.echo("")
    typer.echo("引用：")
    for citation in answer.citations:
        typer.echo(
            f"[{citation.marker}] 《{citation.title}》 来源: {citation.source} "
            f"(得分 {citation.score:.3f})"
        )
        typer.echo(f"    {citation.excerpt[:120]}...")


@section_app.command("create")
def section_create(
    name: str,
    desc: str = typer.Option("", "--desc", help="板块描述"),
) -> None:
    """创建板块。"""
    _, section_repo = build_repos()
    try:
        section = create_section(name, section_repo=section_repo, description=desc)
    except ValueError as exc:
        typer.echo(f"[失败] {exc}")
        raise typer.Exit(code=1) from None
    typer.echo(f"[已创建] 板块《{section.name}》 id={section.section_id}")


@section_app.command("list")
def section_list() -> None:
    """列出全部板块。"""
    _, section_repo = build_repos()
    sections = list_sections(section_repo=section_repo)
    if not sections:
        typer.echo("还没有板块，先用 section create 创建")
        return
    for section in sections:
        desc = f" — {section.description}" if section.description else ""
        typer.echo(f"- {section.name} (id={section.section_id}){desc}")


@section_app.command("update")
def section_update(
    name: str,
    new_name: str = typer.Option(None, "--name", help="新名称"),
    desc: str = typer.Option(None, "--desc", help="新描述"),
) -> None:
    """修改板块的名称或描述。"""
    _, section_repo = build_repos()
    try:
        section = update_section(
            name, section_repo=section_repo, new_name=new_name, description=desc
        )
    except ValueError as exc:
        typer.echo(f"[失败] {exc}")
        raise typer.Exit(code=1) from None
    typer.echo(f"[已更新] 板块《{section.name}》 描述: {section.description or '（无）'}")


@section_app.command("delete")
def section_delete(name: str) -> None:
    """删除板块；板块下的文档回归"未分板块"。"""
    doc_repo, section_repo = build_repos()
    try:
        delete_section(name, section_repo=section_repo, doc_repo=doc_repo)
    except ValueError as exc:
        typer.echo(f"[失败] {exc}")
        raise typer.Exit(code=1) from None
    typer.echo(f"[已删除] 板块《{name}》（其中文档已回归未分板块）")


_SOURCE_LABELS = {
    "session": "会话（仅本次）",
    "env": "环境变量",
    "file": ".env 文件",
    "default": "内置默认",
    "missing": "未设置",
}


@config_app.command("init")
def config_init() -> None:
    """生成无值的 .env 模板；Key 请手动填入，程序绝不代写。"""
    created = build_config_store().init_template()
    if created:
        typer.echo(f"[已生成] {ENV_FILE}（无值模板）")
        typer.echo("请手动把 Key 填进去（该文件不进 git）；也可用环境变量或 --api-key 会话模式")
    else:
        typer.echo(f"[已存在] {ENV_FILE} 未改动（要清某项用 config clear）")


@config_app.command("status")
def config_status() -> None:
    """查看全部配置项的取值来源；Key 一律脱敏显示。"""
    statuses = show_config_status(session=None, env=os.environ, store=build_config_store())
    typer.echo("配置项                 来源            值（Key 已脱敏）")
    for status in statuses:
        source = _SOURCE_LABELS.get(status.source, status.source)
        typer.echo(f"{status.name:<22} {source:<14} {status.display_value}")


@config_app.command("set")
def config_set(name: str, value: str) -> None:
    """写入非密配置（Base URL / Model）到 .env；Key 类一律拒绝落盘。"""
    try:
        var = configure_provider(name, value, store=build_config_store())
    except ValueError as exc:
        typer.echo(f"[失败] {exc}")
        raise typer.Exit(code=1) from None
    typer.echo(f"[已写入] {var} -> {ENV_FILE}")


@config_app.command("clear")
def config_clear(name: str) -> None:
    """清除 .env 中的一项配置。"""
    try:
        var = clear_provider_config(name, store=build_config_store())
    except ValueError as exc:
        typer.echo(f"[失败] {exc}")
        raise typer.Exit(code=1) from None
    typer.echo(f"[已清除] {var}（若环境变量仍设置则优先生效）")


if __name__ == "__main__":
    cli()
