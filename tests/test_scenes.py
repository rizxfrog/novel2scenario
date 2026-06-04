import pytest
from unittest.mock import patch
from backend.pipeline.scenes import analyze_scenes


@pytest.mark.asyncio
async def test_analyze_scenes_parallel():
    chapters = [
        {"number": 1, "title": "Ch1", "content": "The sun rose. Alice walked in."},
        {"number": 2, "title": "Ch2", "content": "Night fell. Bob appeared."},
    ]

    async def mock_analyze_one(**kwargs):
        num = kwargs["number"]
        return {"scenes": [
            {"number": num, "heading": f"INT. Place - Day", "summary": f"Scene {num}",
             "characters_present": ["Alice" if num == 1 else "Bob"],
             "beats": [{"type": "action", "description": f"Action {num}"}]}
        ]}

    with patch("backend.pipeline.scenes._analyze_chapter", side_effect=mock_analyze_one):
        result = await analyze_scenes(chapters)

    assert len(result) == 2
    assert result[0]["summary"] == "Scene 1"
    assert result[1]["summary"] == "Scene 2"
