# Novel2Scenario 剧本 YAML Schema v1

本文档定义了 AI 小说转剧本工具输出的剧本 YAML Schema。

## Schema 概览

```yaml
meta:                    # 元数据
dramatis_personae:       # 角色表（Dramatis Personae）
episodes:                # 剧集列表
adaptation_notes:        # 改编说明
```

## 字段说明

### meta（元数据）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 剧本标题 |
| author | string | 否 | 原作者 |
| total_episodes | integer | 是 | 总集数 |
| total_chapters_in_novel | integer | 是 | 小说原著章节数 |
| generated_at | string | 是 | 生成时间（ISO 8601） |

### dramatis_personae（角色表）

每个角色的字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 角色名 |
| role | enum | 否 | protagonist / antagonist / supporting / minor |
| traits | string[] | 否 | 3-5 个性格特征关键词 |
| description | string | 否 | 外貌与性格描述 |
| first_appearance | integer | 否 | 首次出现的章节编号 |
| relationships | object[] | 否 | 角色关系列表 |

角色关系（relationships 中的每个对象）：

| 字段 | 类型 | 说明 |
|------|------|------|
| with | string | 关联角色名 |
| relation | string | 关系类型 |
| dynamic | string | 关系动态描述 |

### episodes（剧集）

每集的字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| number | integer | 是 | 集号 |
| title | string | 否 | 单集标题 |
| summary | string | 否 | 单集概要 |
| novel_chapters | integer[] | 否 | 改编自小说的哪些章节 |
| scenes | object[] | 是 | 本集的场景列表 |

### scenes（场景）

每个场景的字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 场景唯一 ID（格式：S01E01-01） |
| heading | string | 否 | 场景标题（如 INT. 宫殿大厅 - 日） |
| setting | object | 否 | 场景设定 {location, time_of_day, description} |
| summary | string | 否 | 场景概要 |
| characters_present | string[] | 否 | 出场角色列表 |
| beats | object[] | 是 | 节拍列表 |

### beats（节拍）

每个 beat 的字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | enum | 是 | dialogue / action / direction |
| speaker | string | dialogue 时必填 | 说话者 |
| line | string | dialogue 时必填 | 台词 |
| description | string | action/direction 时必填 | 动作或镜头描述 |

### adaptation_notes（改编说明）

| 字段 | 类型 | 说明 |
|------|------|------|
| type | enum | restructured / omitted / original |
| description | string | 说明文字 |

- restructured：章节内容重新组织
- omitted：删减的内容
- original：新增的内容

## 设计原因

### 1. 扁平层次结构（episodes → scenes → beats）

采用业界标准的剧本结构：剧集包含场景，场景包含节拍。这种三层结构让编剧和导演可以快速定位到任何具体的内容单元。不需要复杂的交叉引用或递归结构。

### 2. beats 使用类型化条目（dialogue / action / direction）

台词、动作和镜头执导是三种根本不同的内容类型。将它们混合在一个文本块中会失去可编辑性。类型化的 beats 允许：
- 按类型渲染（台词用引号，动作用方括号等）
- 按类型过滤统计
- 导入专业剧本软件时的精确映射

### 3. dramatis_personae 前置

标准剧本惯例。在进入具体场景之前，提供所有角色的完整概览，帮助读者快速了解人物阵容。

### 4. adaptation_notes 后置

提供透明度。作者可以看到 AI 对原著做了哪些改变、删减或新增，从而做出明智的修改决策。这是"辅助创作工具"而非"黑盒替换"的核心体现。

### 5. 场景 ID（SxxExx-序号格式）

采用电视剧编号规范。每个场景有全局唯一 ID，方便排序和交叉引用。S01E03-05 表示第一季第三集第五个场景。

### 6. novel_chapters 映射

追溯性。每个剧集可以追溯到它改编自小说的哪些章节，方便作者验证忠实度。

### 7. 角色关系独立存储

角色关系可能不会在对话中直接体现，但对于场景规划和保持一致性至关重要。独立的关系字段帮助 AI 和编剧理解整个故事的人物网络。

## 完整示例

```yaml
meta:
  title: "江湖传奇"
  author: "原作者"
  total_episodes: 24
  total_chapters_in_novel: 42
  generated_at: "2026-06-05T12:00:00Z"

dramatis_personae:
  - name: "林风"
    role: protagonist
    traits: ["勇敢", "正直", "执著"]
    description: "年轻侠客，剑术高超，心怀正义"
    first_appearance: 1
    relationships:
      - with: "苏云"
        relation: "挚友"
        dynamic: "生死之交"
      - with: "黑煞"
        relation: "仇敌"
        dynamic: "杀父之仇"

episodes:
  - number: 1
    title: "初入江湖"
    summary: "少年林风拜别师父，踏上江湖之路"
    novel_chapters: [1, 2]
    scenes:
      - id: "S01E01-01"
        heading: "EXT. 山间小道 - 晨"
        setting:
          location: "青云山"
          time_of_day: "晨"
          description: "云雾缭绕的山间小路"
        characters_present: ["林风", "师父"]
        summary: "林风与师父告别"
        beats:
          - type: action
            description: "林风跪地磕头"
          - type: dialogue
            speaker: "师父"
            line: "江湖险恶，万事小心。"
          - type: dialogue
            speaker: "林风"
            line: "师父放心，徒儿必不负所托。"

adaptation_notes:
  - type: restructured
    description: "第5-7章的内容合并为第3集"
  - type: omitted
    description: "省略了第12章的支线情节"
  - type: original
    description: "第3集的宴会场景为原创"
```
