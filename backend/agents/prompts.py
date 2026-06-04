CHAPTER_SPLIT_PROMPT = """You are analyzing a novel. Split the text below into chapters.
Return a JSON object with this exact structure:
{"title": "小说标题", "author": null, "chapters": [{"number": 1, "title": "章节标题", "content": "..."}]}

Rules:
- Detect chapter boundaries from patterns like "第X章", "Chapter X", or numbered headings
- If no clear delimiters, split at natural scene breaks (every ~2000-3000 words)
- Preserve the full original text within each chapter
- Return ALL chapters found in the input text

Input text:
{text}"""


CHARACTER_EXTRACT_PROMPT = """You are analyzing a single chapter of a novel. Extract all named characters that appear or are mentioned.
Return a JSON object with this exact structure:
{"characters": [{"name": "...", "role": "protagonist|antagonist|supporting|minor", "traits": ["...", "..."], "description": "外貌与性格描述", "first_appearance": 1}]}

Rules:
- role must be one of: protagonist, antagonist, supporting, minor
- traits: 3-5 key personality descriptors
- description: brief physical and personality description in Chinese
- first_appearance: the chapter number this character first appears in
- Include ALL named characters, even minor ones mentioned once
- Do not include unnamed characters like "a servant" or "the crowd"

Chapter {number}: {title}
{content}"""


SCENE_ANALYZE_PROMPT = """You are analyzing a single chapter of a novel to identify individual scenes.
Return a JSON object with this exact structure:
{"title": "章节标题", "scenes": [{"number": 1, "heading": "INT/EXT. 地点 - 时间", "setting": {"location": "...", "time_of_day": "...", "description": "..."}, "summary": "场景摘要", "characters_present": ["角色名"], "beats": [{"type": "dialogue|action|direction", "speaker": "角色名", "line": "台词", "description": "动作/镜头描述"}]}]}

Rules:
- heading: Use standard format like "INT. 地点 - 日" or "EXT. 地点 - 夜"
- scenes are separated by location changes, time jumps, or POV shifts
- beats represent the sequence of events WITHIN a scene
- For dialogue beats: set type="dialogue", include speaker and line
- For action beats: set type="action", include description
- For camera/atmosphere direction: set type="direction", include description
- Keep lines concise and natural

Chapter {number}: {title}
{content}"""


EPISODE_STRUCTURE_PROMPT = """You are structuring a TV drama adaptation from a novel. Given all scenes and characters below, organize them into episodes.
Return a JSON object with this exact structure:
{"episodes": [{"number": 1, "title": "单集标题", "summary": "单集概要", "novel_chapters": [1, 2], "scene_ids": [1, 2, 3, 4]}]}

Rules:
- Each episode should have 5-10 scenes for good pacing
- Group scenes by story arc; each episode should feel like a complete unit
- novel_chapters: list which novel chapters contribute to this episode
- scene_ids: ordered list of scene IDs to include
- Generate a compelling episode title
- Include ALL scenes from the source

Characters:
{characters}

Scenes:
{scenes}"""


SCRIPT_ASSEMBLY_PROMPT = """You are finalizing a TV drama script adapted from a novel. Review the assembled scenes and generate adaptation notes.
Return a JSON object with this exact structure:
{"adaptation_notes": [{"type": "restructured|omitted|original", "description": "说明"}]}

Rules:
- restructured: chapters reorganized for dramatic pacing
- omitted: novel content cut from adaptation
- original: new content not in the novel, created for the adaptation

Characters: {characters}
Episodes: {episodes}"""
