/**
 * Copies the browser-facing ESM builds out of node_modules into static/vendor/,
 * so Django serves them itself and the pages need no CDN and no bundler.
 *
 * static/vendor/ is gitignored — re-create it any time with `npm run sync:vendor`
 * (postinstall runs it automatically).
 */
import { cp, mkdir, readdir, rm, stat } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const from = (...p) => join(root, 'node_modules', ...p);
const to = (...p) => join(root, 'static', 'vendor', ...p);

const jobs = [
  // three.module.js imports './three.core.js', and the .min build imports
  // './three.core.min.js' — each build only works next to its own core file.
  ['three/build/three.module.js', 'three/three.module.js'],
  ['three/build/three.core.js', 'three/three.core.js'],
  ['three/build/three.module.min.js', 'three/three.module.min.js'],
  ['three/build/three.core.min.js', 'three/three.core.min.js'],
  ['three/examples/jsm', 'three/addons'],
  // GSAP ships its ESM entry and every plugin as top-level modules that import
  // each other and utils/; dist/ (UMD), src/ and types/ are not browser-facing.
  ['gsap/utils', 'gsap/utils'],
];

for (const f of await readdir(from('gsap'))) {
  if (f.endsWith('.js')) jobs.push([`gsap/${f}`, `gsap/${f}`]);
}

await rm(to(), { recursive: true, force: true });

let copied = 0;
for (const [src, dest] of jobs) {
  try {
    await stat(from(src));
  } catch {
    console.warn(`  skip (not in node_modules): ${src}`);
    continue;
  }
  await mkdir(dirname(to(dest)), { recursive: true });
  await cp(from(src), to(dest), { recursive: true });
  copied += 1;
}

console.log(`sync-vendor: copied ${copied}/${jobs.length} entries into static/vendor/`);
