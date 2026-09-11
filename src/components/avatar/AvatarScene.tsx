import { useEffect, useMemo, useRef, type RefObject } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import { clone } from 'three/examples/jsm/utils/SkeletonUtils.js';
import { AnimationMixer, Box3, Group, LoopOnce, LoopRepeat, MathUtils, PerspectiveCamera, SkinnedMesh, Vector3 } from 'three';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);
type Props = {
  modelUrl: string; reduced: boolean; active: boolean; waveRequest: number;
  pointer: RefObject<{ x: number; y: number }>;
  host: RefObject<HTMLDivElement | null>; onReady: () => void; onError: () => void;
};

function Character(props: Props) {
  const { scene, animations } = useGLTF(props.modelUrl);
  const { camera, size, invalidate } = useThree();
  const root = useRef<Group>(null);
  const greeted = useRef(false);
  const previousRequest = useRef(0);
  const lockUntil = useRef(0);
  const scroll = useRef({ x: 0 });
  const rig = useMemo(() => {
    const object = clone(scene);
    let skinned = false;
    object.traverse(node => { if ((node as SkinnedMesh).isSkinnedMesh) skinned = true; });
    const idleClip = animations.find(clip => clip.name === 'Idle');
    const waveClip = animations.find(clip => clip.name === 'Wave');
    if (!skinned || !idleClip || !waveClip || idleClip.duration <= 0 || waveClip.duration <= 0) {
      throw new Error('El GLB debe contener una malla con esqueleto y clips Idle y Wave válidos.');
    }
    object.updateMatrixWorld(true);
    const box = new Box3().setFromObject(object, true);
    const height = box.max.y - box.min.y;
    if (!Number.isFinite(height) || height <= 0) throw new Error('Dimensiones del GLB inválidas.');
    const scale = 2 / height;
    const center = box.getCenter(new Vector3());
    const mixer = new AnimationMixer(object);
    // Sample both clips to reserve horizontal space for the extended hand.
    const envelope = box.clone();
    for (const clip of [idleClip, waveClip]) {
      const action = mixer.clipAction(clip).play();
      for (let sample = 0; sample <= 24; sample++) {
        action.time = clip.duration * sample / 24;
        mixer.update(0);
        object.updateMatrixWorld(true);
        envelope.union(new Box3().setFromObject(object, true));
      }
      action.stop();
    }
    const idle = mixer.clipAction(idleClip).setLoop(LoopRepeat, Infinity);
    const wave = mixer.clipAction(waveClip).setLoop(LoopOnce, 1);
    wave.clampWhenFinished = true;
    idle.play();
    mixer.update(0);
    return { object, mixer, idle, wave, scale, offset: [-center.x, -box.min.y, -center.z] as [number, number, number],
      halfWidth: Math.max(envelope.max.x - center.x, center.x - envelope.min.x) * scale,
      top: (envelope.max.y - box.min.y) * scale };
  }, [scene, animations]);

  useEffect(() => {
    const perspective = camera as PerspectiveCamera;
    const mobile = size.width < 400;
    const tablet = size.width < 620;
    const targetY = mobile ? 1.38 : tablet ? 1.4 : 1.42;
    const halfHeight = Math.max(rig.top - targetY, .8);
    const aspect = size.width / Math.max(size.height, 1);
    perspective.fov = mobile ? 36 : tablet ? 33 : 30;
    const distance = Math.max(halfHeight, (rig.halfWidth + .2) / aspect)
      / Math.tan(MathUtils.degToRad(perspective.fov / 2)) * 1.12;
    perspective.position.set(0, targetY, distance);
    perspective.lookAt(0, targetY, 0);
    perspective.updateProjectionMatrix();
    invalidate();
  }, [camera, size.width, size.height, rig, invalidate]);

  useEffect(() => {
    const hero = props.host.current?.closest('.hero');
    if (!hero || props.reduced) { scroll.current.x = 0; invalidate(); return; }
    const tween = gsap.fromTo(scroll.current, { x: .12 }, { x: -.08, ease: 'none',
      onUpdate: invalidate,
      scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: .6, invalidateOnRefresh: true } });
    return () => { tween.scrollTrigger?.kill(); tween.kill(); scroll.current.x = 0; };
  }, [props.reduced, props.host, invalidate]);

  useEffect(() => {
    rig.wave.stop();
    rig.idle.reset().setEffectiveWeight(1).play();
    rig.mixer.update(0);
    lockUntil.current = 0;
    invalidate();
  }, [props.reduced, rig, invalidate]);

  useEffect(() => {
    const finished = () => {
      rig.idle.enabled = true;
      rig.idle.play();
      rig.wave.crossFadeTo(rig.idle, .25, false);
    };
    rig.mixer.addEventListener('finished', finished);
    return () => {
      rig.mixer.removeEventListener('finished', finished);
      rig.mixer.stopAllAction();
      rig.mixer.uncacheRoot(rig.object);
      rig.object.traverse(node => { if ((node as SkinnedMesh).isSkinnedMesh) (node as SkinnedMesh).skeleton.dispose(); });
    };
  }, [rig]);

  const ready = useRef(false);
  useFrame((_, delta) => {
    if (!ready.current) { ready.current = true; props.onReady(); }
    if (!root.current) return;
    if (props.reduced) {
      root.current.rotation.set(0, 0, 0);
      root.current.position.x = 0;
      return;
    }
    const request = previousRequest.current !== props.waveRequest;
    previousRequest.current = props.waveRequest;
    if (props.active && (!greeted.current || request) && rig.mixer.time >= lockUntil.current) {
      greeted.current = true;
      rig.wave.reset().setEffectiveWeight(1).play();
      rig.idle.crossFadeTo(rig.wave, .25, false);
      lockUntil.current = rig.mixer.time + rig.wave.getClip().duration + .8;
    }
    if (props.active) rig.mixer.update(Math.min(delta, .05));
    root.current.position.x = scroll.current.x;
    const limit = MathUtils.degToRad(3);
    root.current.rotation.y = MathUtils.damp(root.current.rotation.y, props.pointer.current.x * limit, 8, delta);
    root.current.rotation.x = MathUtils.damp(root.current.rotation.x, props.pointer.current.y * limit, 8, delta);
  });
  return <group ref={root}><group scale={rig.scale}><group position={rig.offset}>
    <primitive object={rig.object} dispose={null} />
  </group></group></group>;
}

export default function AvatarScene(props: Props) {
  const cleanup = useRef<(() => void) | null>(null);
  useEffect(() => () => cleanup.current?.(), []);
  return <Canvas className="avatar3d-canvas" aria-hidden="true" dpr={[1, 1.5]}
    frameloop={props.reduced || !props.active ? 'demand' : 'always'}
    camera={{ position: [0, 1.4, 4], fov: 33, near: .01, far: 100 }}
    gl={{ alpha: true, antialias: true, powerPreference: 'low-power' }}
    fallback={<span />}
    onCreated={({ gl }) => {
      const canvas = gl.domElement;
      const lost = (event: Event) => { event.preventDefault(); props.onError(); };
      canvas.addEventListener('webglcontextlost', lost);
      cleanup.current = () => canvas.removeEventListener('webglcontextlost', lost);
    }}>
    <ambientLight intensity={1.1} />
    <directionalLight position={[3, 4, 5]} intensity={2.5} />
    <directionalLight position={[-3, 2, -2]} color="#ff7395" intensity={1.4} />
    <Character {...props} />
  </Canvas>;
}
