// Debug helper: rank the index for a query the same way the page does. Usage: node scripts/embed/query.mjs <tab> "<query>" [webDir]
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { pipeline } from '@huggingface/transformers';
const [tab, q, web = 'web'] = process.argv.slice(2);
const idx = JSON.parse(readFileSync(join(web, 'search-index.json'), 'utf8'));
const vec = new Int8Array(readFileSync(join(web, 'search-vectors.bin')).buffer.slice(0));
const ext = await pipeline('feature-extraction', idx.model, { dtype: idx.dtype, revision: idx.revision });
const qv = (await ext(q, { pooling: 'mean', normalize: true })).data;
const T = idx.tabs[tab];
const sims = T.ids.map((id, i) => { let s = 0; const o = (T.offset + i) * idx.dim; for (let k = 0; k < idx.dim; k++) s += qv[k] * vec[o + k]; return [s / idx.scale, id]; });
sims.sort((a, b) => b[0] - a[0]);
const D = JSON.parse(readFileSync(join(web, tab === 'hype' ? 'hype.json' : 'data.json'), 'utf8'));
const items = tab === 'hype' ? D.items : D[tab].items;
for (const [s, id] of sims.slice(0, 6)) console.log(s.toFixed(3), id, '|', (items[id].title || items[id].desc || items[id].name || '').slice(0, 90));
