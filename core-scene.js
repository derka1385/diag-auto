import * as THREE from './vendor/three.module.js';

/** Abstract brand sculpture, deliberately not a mechanical or diagnostic simulation. */
export function mountCore(container) {
  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.setClearColor(0x101214, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.25;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 50);
  camera.position.set(0, 0.7, 8.5);
  camera.lookAt(0, 0, 0);
  const resources = [];
  const own = (resource) => { resources.push(resource); return resource; };

  // A local procedural studio supplies metallic reflections; no remote HDRI.
  const studio = new THREE.Scene();
  studio.background = new THREE.Color(0x303438);
  const panelGeometry = new THREE.PlaneGeometry(1, 1);
  const panelMaterials = [];
  for (const [x, y, z, w, h, color, intensity] of [
    [-4, 3, 2, 3, 8, 0xffffff, 6], [4, 1, 1, 1.2, 7, 0xffffff, 8],
    [0, 5, -2, 6, 3, 0xe9efff, 4], [0, -4, 2, 5, 1, 0xff5c28, 3],
  ]) {
    const material = new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(intensity), side: THREE.DoubleSide });
    panelMaterials.push(material);
    const panel = new THREE.Mesh(panelGeometry, material);
    panel.position.set(x, y, z); panel.scale.set(w, h, 1); panel.lookAt(0, 0, 0); studio.add(panel);
  }
  const pmrem = new THREE.PMREMGenerator(renderer);
  const environment = own(pmrem.fromScene(studio, 0.08));
  scene.environment = environment.texture;
  pmrem.dispose(); panelGeometry.dispose(); panelMaterials.forEach(m => m.dispose());
  scene.add(new THREE.HemisphereLight(0xffffff, 0x201609, 2));
  const key = new THREE.DirectionalLight(0xffffff, 4); key.position.set(-3, 5, 4); scene.add(key);
  const rim = new THREE.PointLight(0xff672d, 40, 12); rim.position.set(2, -1, 2); scene.add(rim);
  const silver = own(new THREE.MeshStandardMaterial({ color: 0xb9bec3, metalness: 1, roughness: 0.21 }));
  const dark = own(new THREE.MeshStandardMaterial({ color: 0x33383d, metalness: 0.95, roughness: 0.27 }));
  const orange = own(new THREE.MeshStandardMaterial({ color: 0xff5c28, metalness: 0.45, roughness: 0.25, emissive: 0xff3d08, emissiveIntensity: 0.25 }));
  const core = new THREE.Group(); scene.add(core); core.rotation.set(0.42, -0.2, -0.36);
  const layers = [];
  for (let i = 0; i < 3; i++) {
    const layer = new THREE.Group();
    const radius = i === 1 ? 1.43 : 1.23;
    const ring = new THREE.Mesh(own(new THREE.TorusGeometry(radius, 0.18, 16, 96)), i === 1 ? dark : silver);
    ring.rotation.x = Math.PI / 2; layer.add(ring);
    const rail = new THREE.Mesh(own(new THREE.TorusGeometry(radius, 0.025, 8, 96)), orange);
    rail.rotation.x = Math.PI / 2; rail.position.y = 0.175; layer.add(rail);
    const discShape = new THREE.Shape();
    discShape.absarc(0, 0, radius - 0.04, 0, Math.PI * 2, false);
    const hole = new THREE.Path(); hole.absarc(0, 0, radius - 0.3, 0, Math.PI * 2, true); discShape.holes.push(hole);
    const plate = new THREE.Mesh(own(new THREE.ExtrudeGeometry(discShape, { depth: 0.09, bevelEnabled: true, bevelSegments: 2, steps: 1, bevelSize: 0.015, bevelThickness: 0.015, curveSegments: 64 })), silver);
    plate.rotation.x = Math.PI / 2; plate.position.y = 0.035; layer.add(plate);
    const tickGeometry = own(new THREE.BoxGeometry(0.025, 0.025, 0.09));
    for (let j = 0; j < 48; j++) {
      const angle = j / 48 * Math.PI * 2;
      const tick = new THREE.Mesh(tickGeometry, j % 12 === 0 ? orange : dark);
      tick.position.set(Math.sin(angle) * (radius - 0.17), 0.065, Math.cos(angle) * (radius - 0.17));
      tick.rotation.y = angle; layer.add(tick);
    }
    core.add(layer); layers.push(layer);
  }
  const spindle = new THREE.Mesh(own(new THREE.CylinderGeometry(0.25, 0.25, 1.9, 6)), dark);
  core.add(spindle);
  const energy = new THREE.Mesh(own(new THREE.IcosahedronGeometry(0.56, 0)), orange);
  energy.scale.y = 1.4; core.add(energy);
  const orbit = new THREE.Mesh(own(new THREE.TorusGeometry(2.18, 0.005, 4, 128)), own(new THREE.MeshBasicMaterial({ color: 0x5e6265, transparent: true, opacity: 0.5 })));
  orbit.rotation.set(0.3, 0.5, 0); core.add(orbit);

  const controls = document.querySelector('#scene-controls');
  const range = document.querySelector('#separation');
  const toggle = document.querySelector('#motion-toggle');
  const preference = matchMedia('(prefers-reduced-motion: reduce)');
  let paused = preference.matches, visible = true, destroyed = false, frame = 0, last = 0, elapsed = 0;
  let pointerX = 0, pointerY = 0;
  const updateButton = () => { toggle.textContent = paused ? 'Resume motion' : 'Pause motion'; toggle.setAttribute('aria-pressed', String(paused)); container.dataset.motion = paused ? 'paused' : 'running'; };
  const draw = () => {
    const spread = 0.56 + Number(range.value) / 100 * 0.63;
    layers.forEach((layer, i) => { layer.position.y = (i - 1) * spread; });
    core.rotation.y = -0.2 + Math.sin(elapsed * 0.24) * 0.24 + pointerX * 0.14;
    core.rotation.x = 0.42 + pointerY * 0.08;
    energy.rotation.y = elapsed * 0.13;
    renderer.render(scene, camera);
  };
  const loop = (now) => {
    frame = 0;
    if (destroyed || paused || !visible || document.hidden) { last = 0; return; }
    if (!last || now - last >= 32) {
      elapsed += last ? Math.min((now - last) / 1000, 0.1) : 0;
      last = now; draw();
    }
    frame = requestAnimationFrame(loop);
  };
  const schedule = () => { if (!frame && !destroyed && !paused && visible && !document.hidden) frame = requestAnimationFrame(loop); };
  const resize = () => {
    const { width, height } = container.getBoundingClientRect();
    if (!width || !height || destroyed) return;
    renderer.setSize(width, height, false); camera.aspect = width / height;
    camera.position.z = camera.aspect < 1 ? 9.3 : 8.5; camera.updateProjectionMatrix(); draw();
  };
  const move = (event) => {
    if (paused || event.pointerType !== 'mouse') return;
    const rect = container.getBoundingClientRect();
    pointerX = (event.clientX - rect.left) / rect.width - 0.5;
    pointerY = (event.clientY - rect.top) / rect.height - 0.5;
  };
  const leave = () => { pointerX = 0; pointerY = 0; };
  const onToggle = () => { paused = !paused; updateButton(); draw(); schedule(); };
  const onPreference = () => { paused = preference.matches; updateButton(); draw(); schedule(); };
  const onVisibility = () => { last = 0; schedule(); };
  const resizeObserver = new ResizeObserver(resize); resizeObserver.observe(container);
  const intersection = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; last = 0; schedule(); }); intersection.observe(container);
  container.appendChild(renderer.domElement); renderer.domElement.setAttribute('aria-hidden', 'true');
  range.addEventListener('input', draw); toggle.addEventListener('click', onToggle);
  container.addEventListener('pointermove', move); container.addEventListener('pointerleave', leave);
  document.addEventListener('visibilitychange', onVisibility); preference.addEventListener('change', onPreference);
  function dispose() {
    if (destroyed) return;
    destroyed = true; cancelAnimationFrame(frame); resizeObserver.disconnect(); intersection.disconnect();
    range.removeEventListener('input', draw); toggle.removeEventListener('click', onToggle);
    container.removeEventListener('pointermove', move); container.removeEventListener('pointerleave', leave);
    document.removeEventListener('visibilitychange', onVisibility); preference.removeEventListener('change', onPreference);
    resources.forEach(resource => resource.dispose()); renderer.dispose(); renderer.domElement.remove();
    container.classList.remove('is-ready'); controls.hidden = true;
    window.removeEventListener('pagehide', onPageHide);
  }
  const onPageHide = (event) => { if (!event.persisted) dispose(); };
  window.addEventListener('pagehide', onPageHide);
  renderer.domElement.addEventListener('webglcontextlost', () => { dispose(); document.querySelector('#scene-caption').textContent = 'STATIC EDITION · 3D CONTEXT UNAVAILABLE'; }, { once: true });
  resize(); updateButton(); controls.hidden = false; container.classList.add('is-ready'); schedule();
  return dispose;
}
