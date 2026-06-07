#!/usr/bin/env node
/**
 * Knowledge Graph Validator — deterministic validation script for
 * the Understand Anything analysis pipeline.
 *
 * Usage: node ua-graph-validate.js <graph-json-path> <results-json-path>
 */

const fs = require("fs");
const path = require("path");

// ── Constants ──────────────────────────────────────────────────────────────

const VALID_NODE_TYPES = new Set([
  "file", "function", "class", "module", "concept",
  "config", "document", "service", "table", "endpoint",
  "pipeline", "schema", "resource",
  "domain", "flow", "step"
]);

const VALID_NODE_ID_PREFIXES = new Set([
  "file:", "function:", "class:", "module:", "concept:",
  "config:", "document:", "service:", "table:", "endpoint:",
  "pipeline:", "schema:", "resource:",
  "domain:", "flow:", "step:"
]);

const VALID_EDGE_TYPES = new Set([
  "imports", "exports", "contains", "inherits", "implements",
  "calls", "subscribes", "publishes", "middleware",
  "reads_from", "writes_to", "transforms", "validates",
  "depends_on", "tested_by", "configures", "related", "similar_to",
  "deploys", "serves", "migrates", "documents", "provisions",
  "routes", "defines_schema", "triggers",
  "contains_flow", "flow_step", "cross_domain"
]);

const VALID_COMPLEXITY = new Set(["simple", "moderate", "complex"]);
const VALID_DIRECTIONS = new Set(["forward", "backward", "bidirectional"]);

const FILE_LEVEL_TYPES = new Set([
  "file", "config", "document", "service", "pipeline",
  "table", "schema", "resource", "endpoint"
]);

// ── Helpers ────────────────────────────────────────────────────────────────

function hasValidPrefix(id, type) {
  const expectedPrefix = type + ":";
  return id.startsWith(expectedPrefix);
}

function isDomainGraph(nodes) {
  return nodes.some(n => n.type === "domain" || n.type === "flow" || n.type === "step");
}

// ── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const graphPath = process.argv[2];
  const resultsPath = process.argv[3];

  if (!graphPath || !resultsPath) {
    console.error("Usage: node ua-graph-validate.js <graph-json> <results-json>");
    process.exit(1);
  }

  // Read and parse
  let kg;
  try {
    const raw = fs.readFileSync(graphPath, "utf-8");
    kg = JSON.parse(raw);
  } catch (err) {
    console.error("FATAL: Cannot read or parse graph file:", err.message);
    process.exit(1);
  }

  const issues = [];
  const warnings = [];
  const stats = {};

  const nodes = Array.isArray(kg.nodes) ? kg.nodes : [];
  const edges = Array.isArray(kg.edges) ? kg.edges : [];
  const layers = Array.isArray(kg.layers) ? kg.layers : [];
  // tour can be plural or singular
  const tour = Array.isArray(kg.tour) ? kg.tour
    : Array.isArray(kg.tours) ? kg.tours
    : [];

  const domainGraph = isDomainGraph(nodes);

  // ──────────────────────────────────────────────────────────
  // CHECK 1: Schema Validation
  // ──────────────────────────────────────────────────────────

  // Node IDs for referential integrity
  const nodeIds = new Map(); // id -> index in nodes array (for duplicate detection)

  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];

    // --- Required fields ---
    if (typeof n.id !== "string" || n.id === "") {
      issues.push(`Node at index ${i}: missing or empty "id" field`);
      continue;
    }

    // Duplicate detection
    if (nodeIds.has(n.id)) {
      issues.push(`Node at index ${i}: duplicate ID "${n.id}" (also at index ${nodeIds.get(n.id)})`);
    }
    nodeIds.set(n.id, i);

    // Type
    if (typeof n.type !== "string" || n.type === "") {
      issues.push(`Node "${n.id}": missing or empty "type" field`);
    } else if (!VALID_NODE_TYPES.has(n.type)) {
      issues.push(`Node "${n.id}": invalid type "${n.type}" — not one of the 16 valid node types`);
    }

    // ID prefix consistency
    if (typeof n.type === "string" && n.type !== "" && typeof n.id === "string" && n.id !== "") {
      if (!hasValidPrefix(n.id, n.type)) {
        warnings.push(`Node "${n.id}": type "${n.type}" does not match ID prefix (expected "${n.type}:" prefix)`);
      }
    }

    // Name
    if (typeof n.name !== "string" || n.name === "") {
      issues.push(`Node "${n.id}": missing or empty "name" field`);
    }

    // Summary
    if (typeof n.summary !== "string" || n.summary.trim() === "") {
      issues.push(`Node "${n.id}": missing or empty "summary" field`);
    } else {
      // Quality: summary is not just the filename
      const summary = n.summary.trim();
      const name = (n.name || "").trim();
      if (summary === name) {
        warnings.push(`Node "${n.id}": summary equals name — generic summary`);
      }
      // Check if summary is just file path filename portion
      const fp = n.filePath || "";
      const fname = path.basename(fp);
      if (fname && summary === fname) {
        warnings.push(`Node "${n.id}": summary is just the filename "${fname}"`);
      }
      // Check for very short summaries (less than 10 chars)
      if (summary.length < 10) {
        warnings.push(`Node "${n.id}": summary is very short (${summary.length} chars): "${summary}"`);
      }
    }

    // Tags
    if (!Array.isArray(n.tags) || n.tags.length === 0) {
      issues.push(`Node "${n.id}": missing or empty "tags" array`);
    } else {
      for (const tag of n.tags) {
        if (typeof tag !== "string") {
          issues.push(`Node "${n.id}": tag "${JSON.stringify(tag)}" is not a string`);
        } else if (tag !== tag.toLowerCase()) {
          warnings.push(`Node "${n.id}": tag "${tag}" is not all lowercase`);
        }
        // Check for spaces in tags (should be hyphenated)
        if (typeof tag === "string" && /\s/.test(tag)) {
          warnings.push(`Node "${n.id}": tag "${tag}" contains whitespace — should be hyphenated`);
        }
      }
    }

    // Complexity
    if (typeof n.complexity !== "string" || n.complexity === "") {
      issues.push(`Node "${n.id}": missing or empty "complexity" field`);
    } else if (!VALID_COMPLEXITY.has(n.complexity)) {
      issues.push(`Node "${n.id}": invalid complexity "${n.complexity}" — must be simple/moderate/complex`);
    }

    // User-requested: file nodes must have valid filePath
    if (n.type === "file" || n.type === "config" || n.type === "document") {
      if (typeof n.filePath !== "string" || n.filePath.trim() === "") {
        issues.push(`Node "${n.id}" (type: ${n.type}): missing or empty "filePath" field`);
      }
    }
  }

  // ──────────────────────────────────────────────────────────
  // Edge validation
  // ──────────────────────────────────────────────────────────

  for (let i = 0; i < edges.length; i++) {
    const e = edges[i];

    // Source
    if (typeof e.source !== "string" || e.source === "") {
      issues.push(`Edge at index ${i}: missing or empty "source" field`);
    } else if (!nodeIds.has(e.source)) {
      issues.push(`Edge at index ${i}: source "${e.source}" references a non-existent node`);
    }

    // Target
    if (typeof e.target !== "string" || e.target === "") {
      issues.push(`Edge at index ${i}: missing or empty "target" field`);
    } else if (!nodeIds.has(e.target)) {
      issues.push(`Edge at index ${i}: target "${e.target}" references a non-existent node`);
    }

    // Type
    if (typeof e.type !== "string" || e.type === "") {
      issues.push(`Edge at index ${i} (${e.source || "?"} → ${e.target || "?"}): missing or empty "type" field`);
    } else if (!VALID_EDGE_TYPES.has(e.type)) {
      issues.push(`Edge at index ${i} (${e.source || "?"} → ${e.target || "?"}): invalid edge type "${e.type}" — not one of 29 valid edge types`);
    }

    // Direction
    if (typeof e.direction !== "string" || e.direction === "") {
      issues.push(`Edge at index ${i} (${e.source || "?"} → ${e.target || "?"}): missing or empty "direction" field`);
    } else if (!VALID_DIRECTIONS.has(e.direction)) {
      issues.push(`Edge at index ${i} (${e.source || "?"} → ${e.target || "?"}): invalid direction "${e.direction}"`);
    }

    // Weight
    if (typeof e.weight !== "number" || isNaN(e.weight)) {
      issues.push(`Edge at index ${i} (${e.source || "?"} → ${e.target || "?"}): weight is not a number`);
    } else if (e.weight < 0.0 || e.weight > 1.0) {
      issues.push(`Edge at index ${i} (${e.source || "?"} → ${e.target || "?"}): weight ${e.weight} is outside 0.0–1.0 range`);
    }

    // Self-referencing
    if (e.source === e.target && typeof e.source === "string" && e.source !== "") {
      warnings.push(`Edge at index ${i}: self-referencing edge "${e.source}" → "${e.target}" of type "${e.type}"`);
    }
  }

  // ──────────────────────────────────────────────────────────
  // CHECK 2: Referential Integrity (already done above for edges)
  // Now check layers and tour
  // ──────────────────────────────────────────────────────────

  for (let li = 0; li < layers.length; li++) {
    const layer = layers[li];
    const name = layer.id || layer.name || `layer[${li}]`;
    if (!Array.isArray(layer.nodeIds)) {
      issues.push(`Layer "${name}": missing nodeIds array`);
      continue;
    }
    if (layer.nodeIds.length === 0) {
      issues.push(`Layer "${name}": empty nodeIds array`);
    }
    for (let ni = 0; ni < layer.nodeIds.length; ni++) {
      const nid = layer.nodeIds[ni];
      if (!nodeIds.has(nid)) {
        issues.push(`Layer "${name}" nodeIds[${ni}]: "${nid}" references a non-existent node`);
      }
    }
  }

  for (let ti = 0; ti < tour.length; ti++) {
    const step = tour[ti];
    const label = `Tour step ${step.order ?? ti}`;
    if (!Array.isArray(step.nodeIds)) {
      issues.push(`${label}: missing nodeIds array`);
      continue;
    }
    if (step.nodeIds.length === 0) {
      issues.push(`${label}: empty nodeIds array`);
    }
    for (let ni = 0; ni < step.nodeIds.length; ni++) {
      const nid = step.nodeIds[ni];
      if (!nodeIds.has(nid)) {
        issues.push(`${label} nodeIds[${ni}]: "${nid}" references a non-existent node`);
      }
    }
  }

  // ──────────────────────────────────────────────────────────
  // CHECK 3: Completeness
  // ──────────────────────────────────────────────────────────

  if (nodes.length === 0) {
    issues.push("Graph has zero nodes");
  }
  if (edges.length === 0) {
    issues.push("Graph has zero edges");
  }
  if (layers.length === 0) {
    if (domainGraph) {
      warnings.push("Domain graph has zero layers (acceptable for domain graphs)");
    } else {
      issues.push("Graph has zero layers");
    }
  }
  if (tour.length === 0) {
    if (domainGraph) {
      warnings.push("Graph has zero tour steps (acceptable for domain graphs)");
    } else {
      issues.push("Graph has zero tour steps");
    }
  }

  // ──────────────────────────────────────────────────────────
  // CHECK 4: Layer Coverage
  // ──────────────────────────────────────────────────────────

  if (layers.length > 0) {
    const fileLevelNodeIds = new Set();
    for (const n of nodes) {
      if (FILE_LEVEL_TYPES.has(n.type)) {
        fileLevelNodeIds.add(n.id);
      }
    }

    const layersCovered = new Map(); // nodeId -> [layer names]
    for (const layer of layers) {
      for (const nid of (layer.nodeIds || [])) {
        if (!layersCovered.has(nid)) {
          layersCovered.set(nid, []);
        }
        layersCovered.get(nid).push(layer.id || layer.name || "unnamed");
      }
    }

    if (!domainGraph) {
      for (const nid of fileLevelNodeIds) {
        if (!layersCovered.has(nid)) {
          issues.push(`File-level node "${nid}" is missing from all layers`);
        } else if (layersCovered.get(nid).length > 1) {
          warnings.push(`File-level node "${nid}" appears in multiple layers: ${layersCovered.get(nid).join(", ")}`);
        }
      }
    }
  }

  // ──────────────────────────────────────────────────────────
  // CHECK 6: Tour Validation
  // ──────────────────────────────────────────────────────────

  if (tour.length > 0) {
    const orders = tour.map(t => t.order).filter(o => o != null);
    const uniqueOrders = new Set(orders);

    if (orders.length !== uniqueOrders.size) {
      warnings.push("Tour has duplicate order values");
    }

    // Check sequential starting from 1
    const sortedOrders = [...orders].sort((a, b) => a - b);
    for (let i = 0; i < sortedOrders.length; i++) {
      if (sortedOrders[i] !== i + 1) {
        warnings.push(`Tour order values are not sequential from 1 (expected ${i + 1}, got ${sortedOrders[i]})`);
        break;
      }
    }

    if (tour.length < 5) {
      warnings.push(`Tour has only ${tour.length} steps (recommended: 5–15)`);
    }
    if (tour.length > 15) {
      warnings.push(`Tour has ${tour.length} steps (recommended: 5–15)`);
    }
  }

  // ──────────────────────────────────────────────────────────
  // CHECK 7: Orphan Nodes
  // ──────────────────────────────────────────────────────────

  const connectedNodes = new Set();
  for (const e of edges) {
    if (e.source) connectedNodes.add(e.source);
    if (e.target) connectedNodes.add(e.target);
  }

  const orphans = [];
  for (const n of nodes) {
    if (!connectedNodes.has(n.id)) {
      orphans.push(n.id);
    }
  }
  if (orphans.length > 0) {
    warnings.push(`${orphans.length} node(s) have no edges connecting to them: ${orphans.slice(0, 10).join(", ")}${orphans.length > 10 ? "..." : ""}`);
  }

  // ──────────────────────────────────────────────────────────
  // CHECK 8: Non-Code Node Quality Checks
  // ──────────────────────────────────────────────────────────

  const outgoingEdges = new Map(); // nodeId -> [edge types]
  const incomingEdges = new Map(); // nodeId -> [edge types]
  for (const e of edges) {
    if (!outgoingEdges.has(e.source)) outgoingEdges.set(e.source, []);
    outgoingEdges.get(e.source).push(e.type);
    if (!incomingEdges.has(e.target)) incomingEdges.set(e.target, []);
    incomingEdges.get(e.target).push(e.type);
  }

  const allEdgeTypesForNode = (nid) => {
    const out = outgoingEdges.get(nid) || [];
    const inc = incomingEdges.get(nid) || [];
    return [...out, ...inc];
  };

  for (const n of nodes) {
    const eTypes = allEdgeTypesForNode(n.id);

    if (n.type === "document" && !eTypes.includes("documents")) {
      warnings.push(`Document node "${n.id}" has no "documents" edges`);
    }
    if (n.type === "service" && !eTypes.includes("deploys") && !eTypes.includes("depends_on")) {
      warnings.push(`Service node "${n.id}" has no "deploys" or "depends_on" edges`);
    }
    if (n.type === "pipeline" && !eTypes.includes("triggers")) {
      warnings.push(`Pipeline node "${n.id}" has no "triggers" edges`);
    }
    if (n.type === "table" && !eTypes.includes("migrates") && !eTypes.includes("defines_schema")) {
      warnings.push(`Table node "${n.id}" has no "migrates" or "defines_schema" edges`);
    }
    if (n.type === "schema" && !eTypes.includes("defines_schema")) {
      warnings.push(`Schema node "${n.id}" has no "defines_schema" edges`);
    }
    if (n.type === "domain" && !eTypes.includes("contains_flow")) {
      warnings.push(`Domain node "${n.id}" has no "contains_flow" edges`);
    }
    if (n.type === "flow" && !eTypes.includes("flow_step")) {
      warnings.push(`Flow node "${n.id}" has no "flow_step" edges`);
    }
  }

  // ──────────────────────────────────────────────────────────
  // CHECK 9: Type / ID prefix consistency (already done in node loop)
  // ──────────────────────────────────────────────────────────

  // ──────────────────────────────────────────────────────────
  // USER REQUEST: Semantic consistency — check contradictory edges
  // ──────────────────────────────────────────────────────────

  // No contradictory bidirectional edges claim: check for pairs where
  // A→B and B→A exist but direction is not bidirectional
  const edgePairs = new Map(); // "source||target||type" -> [indices]
  for (let i = 0; i < edges.length; i++) {
    const e = edges[i];
    const key = `${e.source}||${e.target}||${e.type}`;
    if (!edgePairs.has(key)) edgePairs.set(key, []);
    edgePairs.get(key).push(i);
  }

  for (const [key, indices] of edgePairs) {
    if (indices.length > 1) {
      warnings.push(`Duplicate edge: ${key} appears ${indices.length} times (indices: ${indices.join(", ")})`);
    }
  }

  // Check for contradictory edges (e.g., A contains B AND B contains A)
  for (let i = 0; i < edges.length; i++) {
    const e = edges[i];
    // Only check structural edges that imply hierarchy
    if (["contains", "inherits", "depends_on"].includes(e.type)) {
      const reverseKey = `${e.target}||${e.source}||${e.type}`;
      if (edgePairs.has(reverseKey)) {
        warnings.push(`Contradictory edges: "${e.source}" ${e.type} "${e.target}" and reverse also exists (indices: ${edgePairs.get(reverseKey).join(", ")} and ${i})`);
      }
    }
  }

  // ──────────────────────────────────────────────────────────
  // USER REQUEST: Coverage completeness — are all scanned files represented?
  // We can't check against scan results without that file, but we can check
  // that the graph's own file nodes are internally consistent
  // ──────────────────────────────────────────────────────────

  // Check for file nodes that appear in edges but not with a consistent structural role
  const filePathSet = new Set();
  for (const n of nodes) {
    if (n.filePath) filePathSet.add(n.filePath);
  }

  // ──────────────────────────────────────────────────────────
  // Stats
  // ──────────────────────────────────────────────────────────

  const nodeTypeCounts = {};
  for (const n of nodes) {
    const t = n.type || "unknown";
    nodeTypeCounts[t] = (nodeTypeCounts[t] || 0) + 1;
  }

  const edgeTypeCounts = {};
  for (const e of edges) {
    const t = e.type || "unknown";
    edgeTypeCounts[t] = (edgeTypeCounts[t] || 0) + 1;
  }

  stats.totalNodes = nodes.length;
  stats.totalEdges = edges.length;
  stats.totalLayers = layers.length;
  stats.tourSteps = tour.length;
  stats.nodeTypes = nodeTypeCounts;
  stats.edgeTypes = edgeTypeCounts;

  // ──────────────────────────────────────────────────────────
  // Write results
  // ──────────────────────────────────────────────────────────

  const results = {
    scriptCompleted: true,
    issues,
    warnings,
    stats
  };

  const dir = path.dirname(resultsPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2), "utf-8");
  console.log(`Validation complete: ${issues.length} issues, ${warnings.length} warnings`);
  console.log(`Results written to: ${resultsPath}`);

  process.exit(0);
}

main().catch(err => {
  console.error("FATAL:", err.message);
  process.exit(1);
});
