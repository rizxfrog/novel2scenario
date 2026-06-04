import pytest
from backend.pipeline.splitter import split_chapters, _detect_delimiter

NOVEL_TEXT = """第一章 初入江湖

江南的春天来得特别早。

第二章 风雨欲来

乌云压城，雷鸣隐隐。

第三章 大结局

他终于明白了一切。"""


@pytest.mark.asyncio
async def test_split_by_delimiter():
    chapters = await split_chapters(NOVEL_TEXT)
    assert len(chapters) == 3
    assert chapters[0]["number"] == 1
    assert chapters[0]["title"] == "初入江湖"
    assert "江南的春天" in chapters[0]["content"]
    assert chapters[1]["number"] == 2
    assert chapters[1]["title"] == "风雨欲来"
    assert chapters[2]["number"] == 3
    assert chapters[2]["title"] == "大结局"


def test_detect_delimiter_chinese():
    pattern = _detect_delimiter(NOVEL_TEXT)
    assert pattern is not None
    assert "第" in pattern
