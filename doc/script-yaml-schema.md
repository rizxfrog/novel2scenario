# YAML Script Schema

## Overview

The output of Novel2Scenario is a YAML file containing the complete TV drama script adaptation. This document defines the schema.

## Top-Level Structure

```yaml
meta: {...}
dramatis_personae: [...]
episodes: [...]
adaptation_notes: [...]
```

## Fields

### `meta`

Metadata about the adaptation.

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Title of the adaptation |
| `author` | string? | Original novel author |
| `total_episodes` | integer | Number of episodes generated |
| `total_chapters_in_novel` | integer | Original chapter count |
| `generated_at` | string | ISO 8601 timestamp |

### `dramatis_personae`

Array of character objects.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Character name |
| `role` | string | protagonist / antagonist / supporting / minor |
| `traits` | string[] | Personality traits |
| `description` | string | Physical and personality description |
| `first_appearance` | integer | Chapter number of first appearance |
| `relationships` | array | Relationship objects |

#### Relationship object

| Field | Type | Description |
|-------|------|-------------|
| `with` | string | Related character name |
| `relation` | string | Relationship type |
| `dynamic` | string | Relationship description |

### `episodes`

Array of episode objects.

| Field | Type | Description |
|-------|------|-------------|
| `number` | integer | Episode number |
| `title` | string | Episode title |
| `summary` | string | Episode summary |
| `novel_chapters` | integer[] | Novel chapters covered |
| `scenes` | array | Scene objects |

#### Scene object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Scene ID (e.g., S01E01-01) |
| `heading` | string | Standard heading (INT/EXT. location - time) |
| `setting` | object | Location, time_of_day, description |
| `characters_present` | string[] | Characters in this scene |
| `summary` | string | Scene summary |
| `beats` | array | Beat objects |

#### Beat object

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | dialogue / action / direction |
| `speaker` | string? | Speaker (for dialogue) |
| `line` | string? | Dialogue line |
| `description` | string? | Action or camera description |

### `adaptation_notes`

Array of note objects.

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | restructured / omitted / original |
| `description` | string | Explanation of the adaptation decision |

## Design Rationale

### Why YAML?

YAML is human-readable, supports comments, and is commonly used in the film/TV industry for script tracking. JSON is too verbose for human editing; YAML provides a good balance of structure and readability.

### Scene ID format

Scene IDs use the format `S01E01-02` (Season 01, Episode 01, Scene 02). This makes it easy to reference specific scenes in production and aligns with industry conventions.

### Beat types

- **dialogue**: Spoken lines with a speaker
- **action**: Physical actions performed by characters
- **direction**: Camera directions, lighting notes, and atmospheric descriptions

This three-way split allows the script to serve both as a creative document and as a production planning tool.
