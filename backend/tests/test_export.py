from app.services.notion_service import _markdown_to_notion_blocks


def test_h2_becomes_heading_2_block():
    blocks = _markdown_to_notion_blocks("## My Section")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "heading_2"
    assert blocks[0]["heading_2"]["rich_text"][0]["text"]["content"] == "My Section"


def test_h3_becomes_heading_3_block():
    blocks = _markdown_to_notion_blocks("### Sub Concept")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "heading_3"
    assert blocks[0]["heading_3"]["rich_text"][0]["text"]["content"] == "Sub Concept"


def test_divider_becomes_divider_block():
    blocks = _markdown_to_notion_blocks("---")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "divider"


def test_plain_text_becomes_paragraph_block():
    blocks = _markdown_to_notion_blocks("Some plain text here.")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "paragraph"
    assert "plain text" in blocks[0]["paragraph"]["rich_text"][0]["text"]["content"]


def test_empty_lines_are_skipped():
    blocks = _markdown_to_notion_blocks("Line one\n\n\nLine two")
    assert len(blocks) == 2


def test_bold_markers_are_stripped():
    blocks = _markdown_to_notion_blocks("**Score:** 9/10")
    content = blocks[0]["paragraph"]["rich_text"][0]["text"]["content"]
    assert "**" not in content
    assert "Score:" in content


def test_mixed_markdown_produces_correct_block_types():
    md = "## Title\n### Sub\nSome text\n---\nMore text"
    blocks = _markdown_to_notion_blocks(md)
    types = [b["type"] for b in blocks]
    assert types == ["heading_2", "heading_3", "paragraph", "divider", "paragraph"]
