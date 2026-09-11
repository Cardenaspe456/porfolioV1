import { Component, Suspense, lazy, useEffect, useRef, useState, type ReactNode } from 'react';
import './avatar3d.css';

const Scene = lazy(() => import('./AvatarScene'));
class SceneBoundary extends Component<{ children: ReactNode; onError: () => void }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error: Error) {
    console.warn('Avatar 3D: se muestra el respaldo estático.', error);
    this.props.onError();
  }
  render() { return this.state.failed ? null : this.props.children; }
}

export default function Avatar3D({ modelUrl, posterUrl }: { modelUrl: string; posterUrl: string }) {
  const host = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const [reduced, setReduced] = useState(true);
  const [visible, setVisible] = useState(false);
  const [wave, setWave] = useState(0);
  const pointer = useRef({ x: 0, y: 0 });
  useEffect(() => {
    const query = matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => { setReduced(query.matches); pointer.current = { x: 0, y: 0 }; };
    update();
    query.addEventListener('change', update);
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting));
    if (host.current) observer.observe(host.current);
    return () => { query.removeEventListener('change', update); observer.disconnect(); };
  }, []);
  return <div ref={host} className="avatar3d" data-ready={ready && !failed}>
    <div className="avatar3d-halo" aria-hidden="true" />
    <img className="avatar3d-poster" src={posterUrl} alt="Personaje con cabello rizado y sudadera oscura" />
    {!failed && <SceneBoundary onError={() => setFailed(true)}><Suspense fallback={null}>
      <Scene modelUrl={modelUrl} reduced={reduced} active={visible} waveRequest={wave}
        pointer={pointer} host={host} onReady={() => setReady(true)} onError={() => setFailed(true)} />
    </Suspense></SceneBoundary>}
    {ready && !failed && !reduced && <button type="button" className="avatar3d-control"
      aria-label="Hacer que el avatar salude" onClick={() => setWave(value => value + 1)}
      onPointerEnter={event => { if (event.pointerType === 'mouse') setWave(value => value + 1); }}
      onPointerMove={event => {
        if (event.pointerType !== 'mouse') return;
        const rect = event.currentTarget.getBoundingClientRect();
        pointer.current = { x: Math.max(-1, Math.min(1, (event.clientX - rect.left) / rect.width * 2 - 1)),
          y: Math.max(-1, Math.min(1, (event.clientY - rect.top) / rect.height * 2 - 1)) };
      }} onPointerLeave={() => { pointer.current = { x: 0, y: 0 }; }} />}
  </div>;
}
