#!/usr/bin/env python3
"""Repair critical issues in the knowledge graph JSON."""

import json
import sys

GRAPH_PATH = "d:/Repositories/QNY/novel2scenario/.understand-anything/knowledge-graph.json"
BACKUP_PATH = "d:/Repositories/QNY/novel2scenario/.understand-anything/knowledge-graph.json.bak"

# Load
with open(GRAPH_PATH, "r", encoding="utf-8") as f:
    kg = json.load(f)

changes = []

# ──────────────────────────────────────────────
# Fix 1: Remap invalid node types
# entity → concept, claim → concept
# ──────────────────────────────────────────────
for n in kg.get("nodes", []):
    old_type = n.get("type")
    if old_type == "entity":
        n["type"] = "concept"
        # Also fix ID prefix: entity: → concept:
        old_id = n["id"]
        n["id"] = old_id.replace("entity:", "concept:", 1)
        changes.append(f"Node type: entity→concept, ID: {old_id} → {n['id']}")
    elif old_type == "claim":
        n["type"] = "concept"
        old_id = n["id"]
        n["id"] = old_id.replace("claim:", "concept:", 1)
        changes.append(f"Node type: claim→concept, ID: {old_id} → {n['id']}")

# Build old→new ID mapping for reference updates
node_id_map = {}
for n in kg.get("nodes", []):
    # We need to handle the rename. Let's re-read from the original.
    pass

# Actually let me redo this more carefully with a two-pass approach.
# First pass: build ID map
with open(GRAPH_PATH, "r", encoding="utf-8") as f:
    kg = json.load(f)

id_map = {}
for n in kg.get("nodes", []):
    old_id = n["id"]
    old_type = n.get("type")
    if old_type == "entity":
        n["type"] = "concept"
        n["id"] = old_id.replace("entity:", "concept:", 1)
        id_map[old_id] = n["id"]
        changes.append(f"Node type: entity→concept, ID: {old_id} → {n['id']}")
    elif old_type == "claim":
        n["type"] = "concept"
        n["id"] = old_id.replace("claim:", "concept:", 1)
        id_map[old_id] = n["id"]
        changes.append(f"Node type: claim→concept, ID: {old_id} → {n['id']}")

# Second pass: update all edge references
for e in kg.get("edges", []):
    if e.get("source") in id_map:
        old_src = e["source"]
        e["source"] = id_map[old_src]
    if e.get("target") in id_map:
        old_tgt = e["target"]
        e["target"] = id_map[old_tgt]

# Update layer references
for l in kg.get("layers", []):
    for i, nid in enumerate(l.get("nodeIds", [])):
        if nid in id_map:
            l["nodeIds"][i] = id_map[nid]

# Update tour references
for t in kg.get("tour", []):
    for i, nid in enumerate(t.get("nodeIds", [])):
        if nid in id_map:
            t["nodeIds"][i] = id_map[nid]

# ──────────────────────────────────────────────
# Fix 2: Remap invalid edge types
# builds_on → depends_on, exemplifies → related
# ──────────────────────────────────────────────
for e in kg.get("edges", []):
    old_etype = e.get("type")
    if old_etype == "builds_on":
        e["type"] = "depends_on"
        changes.append(f"Edge type: builds_on→depends_on ({e['source']} → {e['target']})")
    elif old_etype == "exemplifies":
        e["type"] = "related"
        changes.append(f"Edge type: exemplifies→related ({e['source']} → {e['target']})")

# ──────────────────────────────────────────────
# Fix 3: Remove dangling tour references
# Tour step 11 has: Layout.tsx, ProgressBar.tsx, UploadPage.tsx
# ──────────────────────────────────────────────
valid_ids = {n["id"] for n in kg.get("nodes", [])}

for t in kg.get("tour", []):
    if t.get("order") == 11:
        old_len = len(t.get("nodeIds", []))
        t["nodeIds"] = [nid for nid in t.get("nodeIds", []) if nid in valid_ids]
        removed = old_len - len(t["nodeIds"])
        if removed > 0:
            changes.append(f"Tour step 11: removed {removed} dangling node references")

# ──────────────────────────────────────────────
# Save backup and updated graph
# ──────────────────────────────────────────────
import shutil
shutil.copy2(GRAPH_PATH, BACKUP_PATH)

with open(GRAPH_PATH, "w", encoding="utf-8") as f:
    json.dump(kg, f, ensure_ascii=False, indent=2)

print(f"Repairs complete. {len(changes)} changes made:")
for c in changes:
    print(f"  - {c}")
print(f"\nBackup saved to: {BACKUP_PATH}")
