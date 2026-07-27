from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from session_memory.mcp_server.tool_handlers import (
    handle_search_all_workspaces,
    handle_search_conversation_log,
)

mcp = FastMCP("session-memory")


@mcp.tool()
def search_conversation_log(
    query: str,
    top_k: int = 5,
    date_after: Optional[str] = None,
    cwd: Optional[str] = None,
) -> List[dict]:
    """
    Searches this repository's own conversation memory (.conversation-memory/)
    for prior turns relevant to `query`, using hybrid dense+sparse retrieval
    merged via Reciprocal Rank Fusion. Use this when you cannot find the
    rationale for a decision in the project instructions or code, and
    always call it before stating that a past decision was made, to verify
    rather than guess. `date_after` is an optional ISO-8601 timestamp
    restricting results to turns after that time. `cwd` overrides the
    working directory to resolve the workspace from; pass your current
    session's working directory if you track it.
    """
    return handle_search_conversation_log(query, top_k=top_k, date_after=date_after, cwd=cwd)


@mcp.tool()
def search_all_workspaces(
    query: str,
    top_k: int = 5,
    date_after: Optional[str] = None,
    workspaces: Optional[List[str]] = None,
) -> List[dict]:
    """
    Searches conversation memory across every workspace registered on this
    machine (or a subset named/tagged in `workspaces`), for decision
    archaeology across related repositories — e.g. monorepo siblings or
    services that share design decisions. Each result is labeled with its
    source workspace name. Defaults to every registered workspace if
    `workspaces` is omitted.
    """
    return handle_search_all_workspaces(query, top_k=top_k, date_after=date_after, workspaces=workspaces)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
