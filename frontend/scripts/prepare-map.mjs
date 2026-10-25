// Serve the installed, version-matched MapLibre worker locally. No CDN dependency.
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mkdir, copyFile } from 'node:fs/promises';
const require=createRequire(import.meta.url);
const root=dirname(dirname(fileURLToPath(import.meta.url)));
const source=dirname(require.resolve('maplibre-gl/package.json'));
const target=join(root,'public','vendor','maplibre');
await mkdir(target,{recursive:true});
await copyFile(join(source,'dist','maplibre-gl-worker.mjs'),join(target,'maplibre-gl-worker.mjs'));
await copyFile(join(source,'LICENSE.txt'),join(target,'LICENSE.txt'));
console.log('Prepared local MapLibre worker.');
