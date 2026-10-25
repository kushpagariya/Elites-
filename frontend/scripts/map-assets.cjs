// Next loads this during every build, including Vercel's direct `next build`.
const {mkdirSync, copyFileSync} = require('node:fs');
const {dirname, join} = require('node:path');
function prepareMapAssets() {
  const source = dirname(require.resolve('maplibre-gl/package.json'));
  const target = join(__dirname, '..', 'public', 'vendor', 'maplibre');
  mkdirSync(target, {recursive: true});
  for (const name of ['maplibre-gl-worker.mjs', 'LICENSE.txt']) {
    copyFileSync(join(source, name === 'LICENSE.txt' ? '' : 'dist', name), join(target, name));
  }
}
module.exports = {prepareMapAssets};
