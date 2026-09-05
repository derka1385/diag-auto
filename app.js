// Content and contact links work without JavaScript; 3D is progressive enhancement.
const container = document.querySelector('#core-scene');
if (container && !navigator.connection?.saveData) {
  import('./core-scene.js').then(({ mountCore }) => mountCore(container)).catch(() => {
    container.classList.remove('is-ready');
    document.querySelector('#scene-controls').hidden = true;
    document.querySelector('#scene-caption').textContent = 'STATIC EDITION · CONCEPT SCULPTURE';
  });
}
