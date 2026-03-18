"""
Notion integration service.

Current implementation: Internal integration token (personal use).
Migration path to public OAuth: add get_auth_url() and exchange_code_for_token()
here, swap POST /notion/connect for GET /notion/auth-url + GET /notion/callback
in the router. The create_page() function and DB column are unchanged.
"""
import httpx

NOTION_API_VERSION = "2022-06-28"


async def _get_parent_page_id(access_token: str, client: httpx.AsyncClient) -> str:
    """
    Finds the first Notion page shared with this integration to use as a parent.
    Internal integrations cannot create pages at the workspace root — they need
    a parent page that has been shared with them via Connections.
    """
    response = await client.post(
        "https://api.notion.com/v1/search",
        json={"filter": {"value": "page", "property": "object"}, "page_size": 1},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_API_VERSION,
        },
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        raise ValueError(
            "No Notion pages are shared with this integration. "
            "Open a Notion page, click ··· → Connections → add your MasterMind integration."
        )
    return results[0]["id"]


async def create_page(access_token: str, topic: str, markdown_content: str) -> str:
    """
    Creates a new Notion page as a child of the first accessible page.
    Returns the URL of the created page.
    Works with both internal integration tokens and OAuth access tokens.
    """
    blocks = _markdown_to_notion_blocks(markdown_content)

    async with httpx.AsyncClient() as client:
        parent_page_id = await _get_parent_page_id(access_token, client)

        response = await client.post(
            "https://api.notion.com/v1/pages",
            json={
                "parent": {"type": "page_id", "page_id": parent_page_id},
                "properties": {
                    "title": {
                        "title": [{"type": "text", "text": {"content": topic}}]
                    }
                },
                "children": blocks[:100],  # Notion API max 100 blocks per request
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Notion-Version": NOTION_API_VERSION,
            },
        )
        response.raise_for_status()
        return response.json()["url"]


def _markdown_to_notion_blocks(markdown: str) -> list[dict]:
    """
    Converts a Markdown string into Notion block objects.
    Handles: ## headings, ### headings, --- dividers, and paragraphs.
    """
    blocks = []
    for line in markdown.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                },
            })
        elif line.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                },
            })
        elif line == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        else:
            content = line.replace("**", "")
            if content:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    },
                })
    return blocks
