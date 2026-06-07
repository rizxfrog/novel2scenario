const fs = require('fs');
const path = 'd:/Repositories/QNY/novel2scenario/.understand-anything/knowledge-graph.json';

let text = fs.readFileSync(path, 'utf8');

// Find all occurrences of "layers":
const layersPositions = [];
let idx = 0;
const searchStr = '"layers":';
while ((idx = text.indexOf(searchStr, idx)) !== -1) {
  layersPositions.push(idx);
  idx++;
}
console.log('Found layers at positions:', layersPositions);

if (layersPositions.length >= 2) {
  // Find the second layers array end
  const secondLayersStart = layersPositions[1];
  let depth = 0;
  let inString = false;
  let endPos = -1;
  let inArray = false;
  for (let i = secondLayersStart; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"' && (i === 0 || text[i-1] !== '\\')) {
      inString = !inString;
    }
    if (!inString) {
      if (ch === '[') {
        depth++;
        inArray = true;
      } else if (ch === ']') {
        depth--;
        if (depth === 0 && inArray) {
          endPos = i + 1;
          break;
        }
      }
    }
  }
  console.log('Second layers ends at position:', endPos);

  if (endPos > 0) {
    // Find the preceding comma and whitespace
    let removeStart = secondLayersStart;
    while (removeStart > 0) {
      const prev = text[removeStart - 1];
      if (prev === ' ' || prev === '\n' || prev === '\r' || prev === '\t') {
        removeStart--;
      } else if (prev === ',') {
        removeStart--;
        break;
      } else {
        break;
      }
    }

    const newText = text.substring(0, removeStart) + text.substring(endPos);
    fs.writeFileSync(path, newText, 'utf8');
    console.log('Fixed! Removed duplicate layers.');

    // Verify
    const g = JSON.parse(newText);
    console.log('Layers count:', g.layers.length);
    g.layers.forEach(l => console.log('  ' + l.id + ': ' + l.nodeIds.length + ' files - ' + l.name));
    
    // Check total
    const total = g.layers.reduce((s, l) => s + l.nodeIds.length, 0);
    console.log('Total assigned:', total);
  }
} else {
  console.log('Only one layers key found, checking validity...');
  const g = JSON.parse(text);
  console.log('Layers count:', g.layers.length);
}
