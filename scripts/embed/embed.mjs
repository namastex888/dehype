// Semantic search index: one sentence embedding per paper, repo and HYPE project.
// Writes web/search-index.json (ids, model, per-tab offsets) and web/search-vectors.bin (int8, L2-normalised x127).
// The browser embeds only the query with the same model and ranks by dot product. No server, no paid API.
// Usage: node scripts/embed/embed.mjs [webDir]
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
import { pipeline } from '@huggingface/transformers';

export const MODEL = 'Xenova/all-MiniLM-L6-v2';
export const DTYPE = 'q8';
const web = process.argv[2] || 'web';
const D = JSON.parse(readFileSync(join(web, 'data.json'), 'utf8'));
const H = JSON.parse(readFileSync(join(web, 'hype.json'), 'utf8'));

const clip = (s, n) => (s || '').replace(/\s+/g, ' ').trim().slice(0, n);
const docs = {
  papers: Object.entries(D.papers.items).map(([id, p]) => [id, clip(`${p.title}. ${p.tag || ''}. ${p.lab || ''}`, 400)]),
  repos: Object.entries(D.repos.items).map(([id, r]) => [id, clip(`${id.split('/')[1].replace(/[-_]/g, ' ')}: ${r.desc || ''}. ${r.tag || ''}`, 400)]),
  hype: Object.entries(H.items).map(([id, h]) => [id, clip(`${h.name}: ${h.category || ''}. ${h.summary || ''}`, 600)]),
};

const extract = await pipeline('feature-extraction', MODEL, { dtype: DTYPE });
const dim = 384;
const total = Object.values(docs).reduce((a, d) => a + d.length, 0);
const out = new Int8Array(total * dim);
const index = { model: MODEL, dtype: DTYPE, dim, scale: 127, generated_at: new Date().toISOString(),
  data_generated_at: D.generated_at, hype_generated_at: H.generated_at, tabs: {} };
let row = 0;
for (const [tab, list] of Object.entries(docs)) {
  index.tabs[tab] = { offset: row, ids: list.map(([id]) => id) };
  for (let i = 0; i < list.length; i += 64) {
    const batch = list.slice(i, i + 64).map(([, t]) => t);
    const t = await extract(batch, { pooling: 'mean', normalize: true });
    const v = t.data;
    for (let b = 0; b < batch.length; b++, row++)
      for (let k = 0; k < dim; k++) out[row * dim + k] = Math.max(-127, Math.min(127, Math.round(v[b * dim + k] * 127)));
  }
  console.log(`${tab}: ${list.length} embedded`);
}
const bin = Buffer.from(out.buffer);
index.vectors_sha256 = createHash('sha256').update(bin).digest('hex');
index.rows = row;
writeFileSync(join(web, 'search-vectors.bin'), bin);
writeFileSync(join(web, 'search-index.json'), JSON.stringify(index));
console.log(`wrote ${row} vectors (${bin.length} bytes)`);
