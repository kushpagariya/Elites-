'use client';

import dynamic from 'next/dynamic';
import Image from 'next/image';
import { useCallback, useEffect, useId, useRef, useState, type ReactNode } from 'react';
import { animate, motion, useInView, useMotionValue, useReducedMotion, useTransform, type MotionValue } from 'motion/react';

const FilmCity = dynamic(() => import('./City').then(module => module.CinematicCity), { ssr: false });
const duration = 24;

function FilmTitle({ progress, times, opacity, children }: {
  progress: MotionValue<number>; times: number[]; opacity: number[]; children: ReactNode;
}) {
  const alpha = useTransform(progress, times, opacity);
  const transform = useTransform(alpha, [0, 1], ['translate3d(0,18px,0)', 'translate3d(0,0,0)']);
  return <motion.p className="retail-film-title" style={{ opacity: alpha, transform }}>{children}</motion.p>;
}

export default function RetailFilm({ paused }: { paused: boolean }) {
  const frame = useRef<HTMLElement>(null);
  const slider = useRef<HTMLInputElement>(null);
  const id = useId();
  const inView = useInView(frame, { amount: .2 });
  const reduced = useReducedMotion();
  const progress = useMotionValue(0);
  const [playing, setPlaying] = useState(true);
  const [complete, setComplete] = useState(false);
  const [awake, setAwake] = useState(true);
  const [sceneReady, setSceneReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const onReady = useCallback(() => setSceneReady(true), []);
  const onFailure = useCallback(() => setFailed(true), []);
  const active = !paused && !reduced && awake && inView;
  const posterTransform = useTransform(progress, [0, 1], ['scale(1.16) translateX(2%)', 'scale(1.04) translateX(-2%)']);

  useEffect(() => {
    const visibility = () => setAwake(!document.hidden);
    visibility();
    document.addEventListener('visibilitychange', visibility);
    return () => document.removeEventListener('visibilitychange', visibility);
  }, []);

  useEffect(() => progress.on('change', value => {
    if (slider.current) slider.current.value = String(value * 100);
  }), [progress]);

  useEffect(() => {
    if (reduced) { progress.jump(0); setPlaying(false); setComplete(false); }
  }, [reduced, progress]);

  useEffect(() => {
    if (!playing || !active || (!sceneReady && !failed)) return;
    const playback = animate(progress, 1, {
      duration: Math.max(.1, (1 - progress.get()) * duration), ease: 'linear',
      onComplete: () => { setComplete(true); setPlaying(false); },
    });
    return () => playback.stop();
  }, [playing, active, progress, sceneReady, failed]);

  return <section ref={frame} id="retail-film" className="retail-film" aria-labelledby={id}>
    <h2 id={id} className="film-accessible">A cinematic look at your next location</h2>
    <p className="film-accessible">A conceptual retail street, shown through a close-up, a moving street view and a wider network view. This is an illustration.</p>
    <div className="retail-film-picture" aria-hidden="true" data-film-renderer={failed ? 'poster' : sceneReady ? 'webgl' : 'loading'}>
      <motion.div className="retail-film-poster" style={{ transform: paused || reduced ? 'none' : posterTransform }}>
        <Image src="/images/retail-network.png" alt="" fill sizes="100vw"/>
      </motion.div>
      {!reduced && !failed && inView && <div className={'retail-film-world' + (sceneReady ? ' is-ready' : '')}>
        <FilmCity paused={!active || !playing} progress={progress} onFailure={onFailure} onReady={onReady}/>
      </div>}
      <div className="retail-film-letterbox"/>
      <div className="retail-film-titles">
        <FilmTitle progress={progress} times={[0, .25, .32]} opacity={[1, 1, 0]}>Every location<br/>has a story.</FilmTitle>
        <FilmTitle progress={progress} times={[.28, .36, .58, .65]} opacity={[0, 1, 1, 0]}>Beyond the<br/>storefront.</FilmTitle>
        <FilmTitle progress={progress} times={[.62, .72, 1]} opacity={[0, 1, 1]}>Make your<br/>next move.</FilmTitle>
      </div>
    </div>
    {!reduced && <div className="retail-film-controls" role="group" aria-label="Film playback">
      <button type="button" disabled={paused} onClick={() => {
        if (complete) { progress.set(0); setComplete(false); setPlaying(true); }
        else setPlaying(value => !value);
      }}>
        <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none">
          {playing && !paused ? <path d="M8 5v14M16 5v14" stroke="currentColor" strokeWidth="2.5"/> : <path d="m8 5 11 7-11 7V5Z" fill="currentColor"/>}
        </svg>
        {paused ? 'Motion paused' : complete ? 'Replay film' : playing ? 'Pause film' : 'Play film'}
      </button>
      <label className="retail-film-scrubber"><span className="film-accessible">Film position</span>
        <input ref={slider} type="range" min="0" max="100" step=".1" defaultValue="0" disabled={paused}
          onChange={event => {
            const value = Number(event.target.value) / 100;
            setPlaying(false); setComplete(value >= 1); progress.set(value);
          }}/>
      </label>
    </div>}
  </section>;
}
