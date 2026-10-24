'use client';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Component, useEffect, useMemo, useRef, type ReactNode } from 'react';
import * as THREE from 'three';

class SceneBoundary extends Component<{ children: ReactNode; onFailure: () => void }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch() { this.props.onFailure(); }
  render() { return this.state.failed ? null : this.props.children; }
}
type Point = [number, number, number];
function Block({ at, size, color, glow = false }: { at: Point; size: Point; color: string; glow?: boolean }) {
  return <mesh position={at} castShadow receiveShadow><boxGeometry args={size} /><meshStandardMaterial color={color} roughness={.78} emissive={glow ? color : '#000000'} emissiveIntensity={glow ? .35 : 0} /></mesh>;
}
function Sign({ text, at, width = 2, color = '#233c32', ink = '#fff4dc' }: { text: string; at: Point; width?: number; color?: string; ink?: string }) {
  const texture = useMemo(() => {
    const canvas = document.createElement('canvas'); canvas.width = 512; canvas.height = 128;
    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = color; ctx.fillRect(0, 0, 512, 128);
    ctx.fillStyle = ink; ctx.font = 'bold 54px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 256, 68);
    const result = new THREE.CanvasTexture(canvas); result.colorSpace = THREE.SRGBColorSpace; return result;
  }, [text, color, ink]);
  useEffect(() => () => texture.dispose(), [texture]);
  return <mesh position={at}><planeGeometry args={[width, width / 4]} /><meshBasicMaterial map={texture} /></mesh>;
}
function Shop({ x, height, color, name, awning }: { x: number; height: number; color: string; name: string; awning: string }) {
  return <group position={[x, 0, 0]}>
    <Block at={[0, height / 2, 0]} size={[2.6, height, 2]} color={color} />
    <Block at={[0, height + .06, 0]} size={[2.78, .18, 2.18]} color="#f2ddba" />
    <Block at={[0, height + .18, 0]} size={[2.65, .1, 2.05]} color="#c5aa88" />
    {Array.from({ length: 9 }, (_, row) => <Block key={row} at={[0, 2.1 + row * .23, 1.008]} size={[2.6, .018, .012]} color="#d6b29a" />)}
    {[-.7, .7].map((wx) => <group key={wx}>
      <Block at={[wx, height - 1.03, 1.04]} size={[.86, 1.37, .12]} color="#f4e4c9" />
      <Block at={[wx, height - 1.03, 1.12]} size={[.66, 1.15, .06]} color="#294c4b" />
      <Block at={[wx, height - 1.03, 1.16]} size={[.045, 1.16, .04]} color="#e8d8bb" />
      <Block at={[wx, height - 1.03, 1.16]} size={[.67, .045, .04]} color="#e8d8bb" />
      <Block at={[wx, height - 1.74, 1.15]} size={[1, .12, .27]} color="#f4e4c9" />
    </group>)}
    <Block at={[0, .94, 1.035]} size={[2.35, 1.78, .12]} color="#233c32" />
    {[-.8, 0, .8].map((wx) => <group key={wx}>
      <Block at={[wx, .95, 1.12]} size={[.66, 1.53, .04]} color="#f8ba61" glow />
      <Block at={[wx, .62, 1.17]} size={[.66, .05, .06]} color="#775131" />
      <Block at={[wx, .38, 1.2]} size={[.45, .3, .14]} color={wx === 0 ? '#c6783e' : '#eed1a0'} />
    </group>)}
    <Sign text={name} at={[0, 2.02, 1.12]} />
    <group position={[0, 1.82, 1.42]} rotation={[.22, 0, 0]}>
      {Array.from({ length: 10 }, (_, i) => <group key={i}>
        <Block at={[-1.17 + i * .26, 0, 0]} size={[.26, .08, .95]} color={i % 2 ? '#fff0d5' : awning} />
        <Block at={[-1.17 + i * .26, -.13, .45]} size={[.26, .25, .06]} color={i % 2 ? '#fff0d5' : awning} />
      </group>)}
    </group>
    <Block at={[0, .08, 1.25]} size={[2.65, .16, .6]} color="#d6bfa4" />
  </group>;
}
function Tree({ at }: { at: Point }) {
  return <group position={at}>
    <mesh position={[0, .25, 0]} castShadow><cylinderGeometry args={[.29, .21, .5, 12]} /><meshStandardMaterial color="#b65f3a" /></mesh>
    <mesh position={[0, 1.1, 0]} castShadow><cylinderGeometry args={[.07, .1, 1.8, 8]} /><meshStandardMaterial color="#6b5032" /></mesh>
    {[[0, 2, 0], [-.3, 1.8, .1], [.3, 2.2, -.1]].map((p, i) => <mesh key={i} position={p as Point} castShadow><icosahedronGeometry args={[.68, 1]} /><meshStandardMaterial color={['#355e39', '#517644', '#739452'][i]} roughness={1} /></mesh>)}
  </group>;
}
function Street({ paused }: { paused: boolean }) {
  const world = useRef<THREE.Group>(null!);
  const sale = useRef<THREE.Group>(null!);
  const elapsed = useRef(0);
  const { size, camera } = useThree();
  useEffect(() => {
    const cam = camera as THREE.OrthographicCamera;
    cam.zoom = Math.min(size.width / 13.2, size.height / 9.4); cam.updateProjectionMatrix();
    cam.position.set(9, 7.7, 13); cam.lookAt(0, 1.4, .7);
  }, [camera, size]);
  useFrame(({ pointer }, dt) => {
    if (paused || document.hidden) return;
    elapsed.current += Math.min(dt, .04);
    const t = elapsed.current;
    const fine = matchMedia('(pointer: fine)').matches;
    world.current.rotation.y = THREE.MathUtils.damp(world.current.rotation.y, Math.sin(t * .18) * .055 + (fine ? pointer.x * .08 : 0), 4.5, dt);
    sale.current.position.y = 4.7 + Math.sin(t * 1.1) * .15;
    sale.current.rotation.y = Math.sin(t * .7) * .12;
    sale.current.rotation.z = -.12 + Math.sin(t * .9) * .035;
  });
  return <group ref={world} position={[0, -.65, 0]}>
    <Block at={[0, -.24, 1.1]} size={[10.9, .45, 7.1]} color="#b68a67" />
    <Block at={[0, .01, 1.2]} size={[10.9, .09, 6.9]} color="#d0b499" />
    <Block at={[0, .1, .9]} size={[10.8, .16, 3.9]} color="#e4d0ad" />
    {Array.from({ length: 17 }, (_, i) => <Block key={i} at={[-5.1 + i * .64, .068, 3.6]} size={[.025, .008, 1.8]} color="#b7997e" />)}
    {[2.9, 3.5, 4.1].map(z => <Block key={z} at={[0, .07, z]} size={[10.8, .008, .025]} color="#b7997e" />)}
    <Shop x={-3.9} height={4.5} color="#a85742" name="THE CORNER" awning="#274d40" />
    <Shop x={-1.3} height={4.05} color="#d4aa73" name="DAILY GOODS" awning="#aa4930" />
    <Shop x={1.3} height={4.7} color="#a4b6a4" name="MARKET & CO." awning="#274d40" />
    <Shop x={3.9} height={3.8} color="#b97050" name="LOCAL FINDS" awning="#a84b31" />
    {[-4.8, 4.7].map(x => <Tree key={x} at={[x, .2, 2.4]} />)}
    {[-2.7, 2.8].map(x => <group key={x} position={[x, .2, 2.1]}>
      <Block at={[0, 1.2, 0]} size={[.065, 2.4, .065]} color="#263f37" />
      <Block at={[0, 2.45, 0]} size={[.29, .36, .29]} color="#ffdb91" glow />
      <Block at={[0, 2.67, 0]} size={[.4, .08, .4]} color="#263f37" />
    </group>)}
    <group position={[-.5, .22, 2.65]} rotation={[-.12, -.12, 0]}>
      <Block at={[0, .5, 0]} size={[.69, 1, .12]} color="#f6e9cf" />
      <Sign text="SALE" at={[0, .67, .07]} width={.62} color="#a44229" />
      <Sign text="COME IN" at={[0, .36, .07]} width={.56} color="#f6e9cf" ink="#284439" />
    </group>
    <group ref={sale} position={[2.6, 4.7, 2.1]} rotation={[0, 0, -.12]}>
      <Block at={[0, 0, 0]} size={[1.55, .83, .16]} color="#b74628" />
      <Sign text="SALE" at={[0, 0, .09]} width={1.35} color="#b74628" />
    </group>
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -.48, 0]} receiveShadow><planeGeometry args={[200, 200]} /><shadowMaterial transparent opacity={.16} /></mesh>
  </group>;
}
export default function City({ paused, onFailure }: { paused: boolean; onFailure: () => void }) {
  return <SceneBoundary onFailure={onFailure}><Canvas shadows orthographic camera={{ position: [9, 7.7, 13], zoom: 55, near: .1, far: 100 }} dpr={[1, 1.5]} frameloop={paused ? 'demand' : 'always'} gl={{ antialias: true, alpha: true, powerPreference: 'low-power' }} onCreated={({ gl }) => { gl.domElement.addEventListener('webglcontextlost', onFailure, { once: true }); }}>
    <ambientLight intensity={1.6} />
    <directionalLight castShadow position={[-4, 10, 8]} intensity={2.5} color="#ffe4b7" shadow-mapSize={[1024, 1024]} shadow-camera-left={-12} shadow-camera-right={12} shadow-camera-top={12} shadow-camera-bottom={-12} shadow-normalBias={.04} />
    <directionalLight position={[5, 5, -4]} intensity={1.2} color="#d4e7e3" />
    <Street paused={paused} />
  </Canvas></SceneBoundary>;
}
