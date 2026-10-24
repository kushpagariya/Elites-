'use client';

import { useEffect, useRef, type ReactNode, type RefObject } from 'react';
import { motion, useMotionValue, useScroll, useSpring, useTransform } from 'motion/react';

const easeOut = 'cubic-bezier(0.23, 1, 0.32, 1)';
const pointerSpring = { mass: 1, stiffness: 100, damping: 10 };

/** Decorative cartography only. It does not represent locations or model output. */
export function ExpansionField({ children, paused }: { children: ReactNode; paused: boolean }) {
  const stage = useRef<HTMLDivElement>(null);
  const finePointer = useRef(false);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const x = useSpring(mouseX, pointerSpring);
  const y = useSpring(mouseY, pointerSpring);
  const { scrollYProgress } = useScroll({ target: stage, offset: ['start start', 'end start'] });

  const passTransform = useTransform<number, string>([x, y, scrollYProgress], ([px, py, progress]) =>
    `perspective(1100px) translate3d(${px * 10}px,${py * 7 + progress * 32}px,0) rotateX(${-py * 3 - progress * 4}deg) rotateY(${px * 4}deg) rotateZ(${-progress * 3}deg) scale(${1 - progress * .04})`,
  );
  const fieldTransform = useTransform<number, string>([x, y, scrollYProgress], ([px, py, progress]) =>
    `translate3d(${-px * 18}px,${-py * 12 - progress * 24}px,0) rotate(${-progress * 8}deg) scale(${1 + progress * .08})`,
  );

  useEffect(() => {
    const query = matchMedia('(hover: hover) and (pointer: fine)');
    const update = () => {
      finePointer.current = query.matches;
      mouseX.set(0);
      mouseY.set(0);
    };
    update();
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, [mouseX, mouseY]);

  useEffect(() => {
    if (paused) {
      mouseX.jump(0);
      mouseY.jump(0);
      x.jump(0);
      y.jump(0);
    }
  }, [paused, mouseX, mouseY, x, y]);

  return (
    <div
      ref={stage}
      className="expansion-stage"
      data-field-paused={paused}
      onPointerMove={event => {
        if (paused || !finePointer.current || event.pointerType !== 'mouse') return;
        const bounds = event.currentTarget.getBoundingClientRect();
        mouseX.set(Math.max(-1, Math.min(1, (event.clientX - bounds.left) / bounds.width * 2 - 1)));
        mouseY.set(Math.max(-1, Math.min(1, (event.clientY - bounds.top) / bounds.height * 2 - 1)));
      }}
      onPointerLeave={() => { mouseX.set(0); mouseY.set(0); }}
    >
      <motion.div className="expansion-field" style={{ transform: paused ? 'none' : fieldTransform }} aria-hidden="true">
        <svg viewBox="0 0 640 640" fill="none" className="expansion-cartography">
          <g className="expansion-streets" strokeLinecap="round" strokeLinejoin="round">
            <path d="M58 190H176V100H394V166H558V410H482V534H282V482H90V356H146V278H58"/>
            <path d="M94 100V294H280V534M58 356H546M176 190H482V94M394 166V482H558"/>
            <path d="M90 440H210V230H460V165H540" className="expansion-route"/>
          </g>
          <g className="expansion-pin expansion-pin-a"><circle cx="94" cy="190" r="17" className="expansion-radius"/><circle cx="94" cy="190" r="5"/></g>
          <g className="expansion-pin expansion-pin-b"><circle cx="540" cy="165" r="17" className="expansion-radius"/><circle cx="540" cy="165" r="5"/></g>
          <g className="expansion-pin expansion-pin-c"><circle cx="90" cy="440" r="17" className="expansion-radius"/><circle cx="90" cy="440" r="5"/></g>
          <g className="expansion-pin expansion-pin-d"><circle cx="482" cy="482" r="17" className="expansion-radius"/><circle cx="482" cy="482" r="5"/></g>
          <circle r="5" className="expansion-signal"/>
        </svg>
      </motion.div>
      <motion.div className="expansion-pass" style={{ transform: paused ? 'none' : passTransform }}>
        {children}
      </motion.div>
    </div>
  );
}

/** Finite, once-per-visit reveals. Content is visible without JS or animation support. */
export function useLandingChoreography(root: RefObject<HTMLDivElement | null>, paused: boolean) {
  const played = useRef(new WeakSet<Element>());

  useEffect(() => {
    const surface = root.current;
    if (!surface || paused || !Element.prototype.animate || !window.IntersectionObserver) return;
    const animations = new Set<Animation>();
    const play = (element: Element, frames: Keyframe[], duration: number, delay = 0) => {
      const animation = element.animate(frames, { duration, delay, easing: easeOut, fill: 'none' });
      animations.add(animation);
      animation.onfinish = () => animations.delete(animation);
    };
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting || played.current.has(entry.target)) continue;
        played.current.add(entry.target);
        observer.unobserve(entry.target);
        if (entry.target.matches('.editorial-visual')) {
          const picture = entry.target.querySelector('img');
          if (picture) play(picture, [
            { transform: 'scale(1.035)', clipPath: 'inset(7% 3% 7% 3% round 16px)' },
            { transform: 'scale(1)', clipPath: 'inset(0% 0% 0% 0% round 16px)' },
          ], 1000);
        } else if (entry.target.matches('.journey-steps, .evidence-pillars-grid')) {
          Array.from(entry.target.children).forEach((item, index) => play(item, [
            { opacity: .6, transform: 'translate3d(0,24px,0)' },
            { opacity: 1, transform: 'translate3d(0,0,0)' },
          ], 650, index * 100));
        } else {
          play(entry.target, [
            { opacity: .65, transform: 'translate3d(0,22px,0)' },
            { opacity: 1, transform: 'translate3d(0,0,0)' },
          ], 700);
        }
      }
    }, { threshold: .15 });
    surface.querySelectorAll('.section-heading-row h2, .section-header-block h2, .journey-steps, .editorial-visual, .evidence-pillars-grid').forEach(element => {
      if (!played.current.has(element)) observer.observe(element);
    });
    const visibility = () => {
      for (const animation of animations) {
        if (document.hidden) animation.pause();
        else animation.play();
      }
    };
    document.addEventListener('visibilitychange', visibility);
    return () => {
      observer.disconnect();
      document.removeEventListener('visibilitychange', visibility);
      for (const animation of animations) animation.cancel();
    };
  }, [root, paused]);
}
