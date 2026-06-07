const fs = require('fs');

const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const { fileNodes, importEdges, allEdges } = input;

// Helper: resolve path prefix for directory grouping
function getDirGroup(filePath) {
  const parts = filePath.replace(/\\/g, '/').split('/');
  if (parts.length === 1) return 'root';
  // Get first segment after common root detection
  return parts[0];
}

// A. Directory Grouping
const directoryGroups = {};
for (const node of fileNodes) {
  const dir = getDirGroup(node.filePath);
  if (!directoryGroups[dir]) directoryGroups[dir] = [];
  directoryGroups[dir].push(node.id);
}

// B. Node Type Grouping
const nodeTypeGroups = {};
for (const node of fileNodes) {
  const t = node.type;
  if (!nodeTypeGroups[t]) nodeTypeGroups[t] = [];
  nodeTypeGroups[t].push(node.id);
}

// C. Import adjacency matrix - fan-in, fan-out
const fanOut = {};
const fanIn = {};
for (const node of fileNodes) {
  fanOut[node.id] = 0;
  fanIn[node.id] = 0;
}
for (const edge of importEdges) {
  if (fanOut[edge.source] !== undefined) fanOut[edge.source]++;
  if (fanIn[edge.target] !== undefined) fanIn[edge.target]++;
}

// Group-level import sets
const groupImportsFrom = {}; // group -> Set of groups it imports from
const groupImportsTo = {};   // group -> Set of groups that import it
for (const dir of Object.keys(directoryGroups)) {
  groupImportsFrom[dir] = new Set();
  groupImportsTo[dir] = new Set();
}
const idToGroup = {};
for (const [dir, ids] of Object.entries(directoryGroups)) {
  for (const id of ids) {
    idToGroup[id] = dir;
  }
}
for (const edge of importEdges) {
  const srcGroup = idToGroup[edge.source];
  const tgtGroup = idToGroup[edge.target];
  if (srcGroup && tgtGroup && srcGroup !== tgtGroup) {
    groupImportsFrom[srcGroup].add(tgtGroup);
    groupImportsTo[tgtGroup].add(srcGroup);
  }
}

// D. Cross-Category Dependency Analysis (using allEdges)
const crossCategoryEdges = [];
const ccMap = {};
for (const edge of allEdges) {
  const srcNode = fileNodes.find(n => n.id === edge.source);
  const tgtNode = fileNodes.find(n => n.id === edge.target);
  if (!srcNode || !tgtNode) continue;
  const fromType = srcNode.type;
  const toType = tgtNode.type;
  const key = `${fromType}->${toType}:${edge.type}`;
  ccMap[key] = (ccMap[key] || 0) + 1;
}
for (const [key, count] of Object.entries(ccMap)) {
  const [ft, rest] = key.split('->');
  const [tt, et] = rest.split(':');
  crossCategoryEdges.push({ fromType: ft, toType: tt, edgeType: et, count });
}

// E. Inter-Group Import Frequency
const interGroupImports = [];
const igMap = {};
for (const edge of importEdges) {
  const srcGroup = idToGroup[edge.source];
  const tgtGroup = idToGroup[edge.target];
  if (srcGroup && tgtGroup && srcGroup !== tgtGroup) {
    const key = `${srcGroup}->${tgtGroup}`;
    igMap[key] = (igMap[key] || 0) + 1;
  }
}
for (const [key, count] of Object.entries(igMap)) {
  const [from, to] = key.split('->');
  interGroupImports.push({ from, to, count });
}

// F. Intra-Group Import Density
const intraGroupDensity = {};
for (const [dir, ids] of Object.entries(directoryGroups)) {
  const idSet = new Set(ids);
  let internalEdges = 0;
  let totalEdges = 0;
  for (const edge of importEdges) {
    const inSrc = idSet.has(edge.source);
    const inTgt = idSet.has(edge.target);
    if (inSrc && inTgt) internalEdges++;
    if (inSrc || inTgt) totalEdges++;
  }
  intraGroupDensity[dir] = {
    internalEdges,
    totalEdges,
    density: totalEdges > 0 ? internalEdges / totalEdges : 0
  };
}

// G. Directory Pattern Matching
const patternMap = {
  'routes': 'api', 'api': 'api', 'controllers': 'api', 'endpoints': 'api', 'handlers': 'api',
  'services': 'service', 'core': 'service', 'lib': 'service', 'domain': 'service', 'logic': 'service',
  'models': 'data', 'db': 'data', 'data': 'data', 'persistence': 'data', 'repository': 'data', 'entities': 'data',
  'components': 'ui', 'views': 'ui', 'pages': 'ui', 'ui': 'ui', 'layouts': 'ui', 'screens': 'ui',
  'middleware': 'middleware', 'plugins': 'middleware', 'interceptors': 'middleware', 'guards': 'middleware',
  'utils': 'utility', 'helpers': 'utility', 'common': 'utility', 'shared': 'utility', 'tools': 'utility',
  'config': 'config', 'constants': 'config', 'env': 'config', 'settings': 'config',
  'tests': 'test', 'test': 'test', 'spec': 'test', 'specs': 'test',
  'types': 'types', 'interfaces': 'types', 'schemas': 'types', 'contracts': 'types', 'dtos': 'types',
  'hooks': 'hooks', 'store': 'state', 'state': 'state', 'reducers': 'state',
  'assets': 'assets', 'static': 'assets', 'public': 'assets',
  'migrations': 'data', 'management': 'config', 'commands': 'config',
  'templatetags': 'utility', 'signals': 'service', 'serializers': 'api',
  'cmd': 'entry', 'internal': 'service', 'pkg': 'utility',
  'dto': 'types', 'request': 'types', 'response': 'types', 'entity': 'data',
  'controller': 'api', 'routers': 'api', 'composables': 'service',
  'blueprints': 'api', 'mailers': 'service', 'jobs': 'service', 'channels': 'service',
  'bin': 'entry', 'docs': 'documentation', 'documentation': 'documentation', 'wiki': 'documentation',
  'deploy': 'infrastructure', 'deployment': 'infrastructure', 'infra': 'infrastructure', 'infrastructure': 'infrastructure',
  'kubernetes': 'infrastructure', 'k8s': 'infrastructure', 'helm': 'infrastructure', 'charts': 'infrastructure',
  'terraform': 'infrastructure', 'tf': 'infrastructure', 'docker': 'infrastructure',
  'sql': 'data', 'database': 'data', 'schema': 'data',
  'pipeline': 'service', 'agents': 'service', 'context': 'state',
  'stages': 'ui', 'backend': 'service', 'frontend': 'ui',
  'doc': 'documentation', 'superpowers': 'documentation',
};

// File-level pattern matching
function getFilePattern(filePath, name) {
  if (name.match(/\.test\./) || name.match(/\.spec\./) || name.match(/^test_/) || name.match(/_test\./) || name.match(/Test\.(java|php|cs)$/) || name.match(/_spec\.rb$/) || name.match(/Tests\.cs$/)) return 'test';
  if (name.endsWith('.d.ts')) return 'types';
  if ((name === 'index.ts' || name === 'index.js' || name === '__init__.py') && filePath.includes('/')) return 'entry';
  if (name === 'manage.py' && !filePath.includes('/')) return 'entry';
  if (name === 'wsgi.py' || name === 'asgi.py') return 'config';
  if (name.endsWith('.sql')) return 'data';
  if (name.endsWith('.graphql') || name.endsWith('.gql') || name.endsWith('.proto')) return 'types';
  if (name.endsWith('.md') || name.endsWith('.rst')) return 'documentation';
  if (name === 'Dockerfile' || name.startsWith('docker-compose')) return 'infrastructure';
  if (name.endsWith('.tf') || name.endsWith('.tfvars')) return 'infrastructure';
  if (name === 'Makefile') return 'infrastructure';
  if (name === 'Cargo.toml' || name === 'go.mod' || name === 'Gemfile' || name === 'pom.xml' || name === 'build.gradle' || name === 'composer.json') return 'config';
  if (name === 'pyproject.toml') return 'config';
  if (name === 'package.json' || name === 'tsconfig.json') return 'config';
  if (name.endsWith('.module.css')) return 'ui';
  if (name.endsWith('.css')) return 'ui';
  if (name === 'index.html') return 'ui';
  if (name.endsWith('.env') || name === '.env.example') return 'config';
  if (name === '.python-version') return 'config';
  if (name === 'vite.config.ts') return 'config';
  if (name === 'api.ts') return 'service';
  if (name === 'reducer.ts') return 'state';
  return null;
}

const patternMatches = {};
for (const [dir] of Object.entries(directoryGroups)) {
  patternMatches[dir] = patternMap[dir] || null;
}
// Also check subdirs in paths
const subDirPatterns = {};
for (const node of fileNodes) {
  const parts = node.filePath.replace(/\\/g, '/').split('/');
  for (let i = 0; i < parts.length - 1; i++) {
    const seg = parts[i];
    if (patternMap[seg] && !subDirPatterns[seg]) {
      subDirPatterns[seg] = patternMap[seg];
    }
  }
}
// Merge subdir patterns into patternMatches
for (const [seg, pat] of Object.entries(subDirPatterns)) {
  if (!patternMatches[seg]) patternMatches[seg] = pat;
}
// Apply file-level patterns as overrides for groups that are null
for (const [dir] of Object.entries(directoryGroups)) {
  if (!patternMatches[dir]) {
    // Check files in this group for patterns
    for (const node of fileNodes) {
      const g = getDirGroup(node.filePath);
      if (g === dir) {
        const fp = node.filePath;
        const name = node.name;
        const pat = getFilePattern(fp, name);
        if (pat) {
          patternMatches[dir] = pat;
          break;
        }
      }
    }
  }
}

// H. Deployment Topology Detection
const deploymentTopology = {
  hasDockerfile: false,
  hasCompose: false,
  hasK8s: false,
  hasTerraform: false,
  hasCI: false,
  infraFiles: []
};
for (const node of fileNodes) {
  const fp = node.filePath;
  const name = node.name;
  if (name === 'Dockerfile') { deploymentTopology.hasDockerfile = true; deploymentTopology.infraFiles.push(fp); }
  if (name.startsWith('docker-compose')) { deploymentTopology.hasCompose = true; deploymentTopology.infraFiles.push(fp); }
  if (fp.includes('kubernetes') || fp.includes('/k8s/') || fp.includes('/helm/')) { deploymentTopology.hasK8s = true; deploymentTopology.infraFiles.push(fp); }
  if (name.endsWith('.tf') || name.endsWith('.tfvars')) { deploymentTopology.hasTerraform = true; deploymentTopology.infraFiles.push(fp); }
  if (fp.includes('.github/workflows') || name === '.gitlab-ci.yml' || name === 'Jenkinsfile') { deploymentTopology.hasCI = true; deploymentTopology.infraFiles.push(fp); }
}

// I. Data Pipeline Detection
const dataPipeline = {
  schemaFiles: [],
  migrationFiles: [],
  dataModelFiles: [],
  apiHandlerFiles: []
};
for (const node of fileNodes) {
  const fp = node.filePath;
  const name = node.name;
  if (name.endsWith('.sql')) dataPipeline.schemaFiles.push(fp);
  if (fp.includes('migration')) dataPipeline.migrationFiles.push(fp);
  if (fp.includes('models') || fp.includes('entities') || fp.includes('schema')) {
    if (name.endsWith('.py') || name.endsWith('.ts')) dataPipeline.dataModelFiles.push(fp);
  }
  if (fp.includes('routes') || fp.includes('controllers') || fp.includes('handlers') || fp.includes('endpoints')) {
    dataPipeline.apiHandlerFiles.push(fp);
  }
}

// J. Documentation Coverage
const groupsWithDocs = [];
const undocumentedGroups = [];
for (const [dir, ids] of Object.entries(directoryGroups)) {
  let hasDoc = false;
  for (const id of ids) {
    const node = fileNodes.find(n => n.id === id);
    if (node && (node.type === 'document' || node.filePath.match(/README\.(md|rst)/i) || node.filePath.match(/\.(md|rst)$/))) {
      hasDoc = true;
      break;
    }
  }
  if (hasDoc) groupsWithDocs.push(dir);
  else undocumentedGroups.push(dir);
}
const docCoverage = {
  groupsWithDocs: groupsWithDocs.length,
  totalGroups: Object.keys(directoryGroups).length,
  coverageRatio: Object.keys(directoryGroups).length > 0 ? groupsWithDocs.length / Object.keys(directoryGroups).length : 0,
  undocumentedGroups
};

// K. Dependency Direction
const dependencyDirection = [];
for (const [key, count] of Object.entries(igMap)) {
  const [from, to] = key.split('->');
  const reverseKey = `${to}->${from}`;
  const reverseCount = igMap[reverseKey] || 0;
  if (count > reverseCount) {
    dependencyDirection.push({ dependent: from, dependsOn: to });
  }
}

// File stats
const filesPerGroup = {};
for (const [dir, ids] of Object.entries(directoryGroups)) {
  filesPerGroup[dir] = ids.length;
}
const nodeTypeCounts = {};
for (const [t, ids] of Object.entries(nodeTypeGroups)) {
  nodeTypeCounts[t] = ids.length;
}

const output = {
  scriptCompleted: true,
  directoryGroups,
  nodeTypeGroups,
  crossCategoryEdges,
  interGroupImports,
  intraGroupDensity,
  patternMatches,
  deploymentTopology,
  dataPipeline,
  docCoverage,
  dependencyDirection,
  fileStats: {
    totalFileNodes: fileNodes.length,
    filesPerGroup,
    nodeTypeCounts
  },
  fileFanIn: fanIn,
  fileFanOut: fanOut
};

fs.writeFileSync(process.argv[3], JSON.stringify(output, null, 2));
console.log(`Analysis complete: ${fileNodes.length} files, ${importEdges.length} import edges, ${Object.keys(directoryGroups).length} groups`);
