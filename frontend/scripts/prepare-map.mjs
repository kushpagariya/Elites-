// Serve the installed, version-matched MapLibre worker locally. No CDN dependency.
import assets from './map-assets.cjs';
assets.prepareMapAssets();
console.log('Prepared local MapLibre worker.');
