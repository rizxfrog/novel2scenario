import pytest
from unittest.mock import patch
from backend.pipeline.assembler import assemble_script


@pytest.mark.asyncio
async def test_assemble_script():
    meta = {"title": "Test Novel", "author": "Author", "total_chapters_in_novel": 3}
    characters = [{"name": "Alice", "role": "protagonist", "traits": ["brave"], "description": "Hero", "first_appearance": 1, "relationships": []}]
    episodes = [{"number": 1, "title": "E1", "summary": "...", "novel_chapters": [1, 2], "scene_ids": [1, 2]}]
    scenes = [
        {"id": 1, "heading": "INT. Room - Day", "summary": "Start", "characters_present": ["Alice"],
         "beats": [{"type": "action", "description": "She enters"}]}
    ]

    async def mock_agent(*args, **kwargs):
        return {"adaptation_notes": [{"type": "restructured", "description": "Merged chapters"}]}

    with patch("backend.pipeline.assembler.run_agent", side_effect=mock_agent):
        script = await assemble_script(meta, characters, episodes, scenes)

    assert "meta" in script
    assert script["meta"]["title"] == "Test Novel"
    assert len(script["episodes"]) == 1
    assert len(script["adaptation_notes"]) == 1
