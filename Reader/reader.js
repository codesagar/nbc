(() => {
  'use strict';
  document.documentElement.classList.add('js');
  const key = 'neet-buddy-reader-v1';
  let state = {};
  try { const stored = JSON.parse(localStorage.getItem(key) || '{}'); if (stored && typeof stored === 'object' && !Array.isArray(stored)) state = stored; } catch (_) {}
  const save = () => { try { localStorage.setItem(key, JSON.stringify(state)); } catch (_) {} };
  const apply = () => {
    document.documentElement.classList.toggle('night', state.night === true);
    document.documentElement.style.setProperty('--reading-size', `${Math.max(18, Math.min(27, state.size || 21))}px`);
    const theme = document.querySelector('[data-theme]');
    if (theme) { theme.textContent = state.night ? 'Day' : 'Night'; theme.setAttribute('aria-pressed', String(state.night === true)); }
  };
  apply();
  document.querySelector('[data-theme]')?.addEventListener('click', () => { state.night = !state.night; apply(); save(); });
  document.querySelectorAll('[data-font]').forEach(button => button.addEventListener('click', () => {
    state.size = Math.max(18, Math.min(27, (state.size || 21) + Number(button.dataset.font))); apply(); save();
  }));
  const cards = [...document.querySelectorAll('.card')];
  if (cards.length) {
    let group = 'all';
    const search = document.querySelector('#search');
    const filter = () => {
      const query = search.value.trim().toLocaleLowerCase(); let shown = 0;
      cards.forEach(card => { const match = (group === 'all' || card.dataset.group === group) && card.dataset.search.includes(query); card.hidden = !match; if (match) shown++; });
      document.querySelector('#result-count').textContent = `${shown} ${shown === 1 ? 'story' : 'stories'}`;
      document.querySelector('#no-results').hidden = shown > 0;
    };
    search.addEventListener('input', filter);
    document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
      group = button.dataset.filter;
      document.querySelectorAll('[data-filter]').forEach(b => b.setAttribute('aria-pressed', String(b === button))); filter();
    }));
    cards.forEach(card => { if (state.read?.[card.dataset.id]) card.querySelector('.read-badge').hidden = false; });
    const resume = document.querySelector('#resume');
    // The stored URL is accepted only if it names a page in this generated collection.
    const validPages = (document.body.dataset.pages || '').split('|');
    if (state.last && validPages.includes(state.last.page)) {
      resume.href = `${state.last.page}#resume`; resume.textContent = `Continue: ${state.last.title}`; resume.hidden = false;
    }
  }
  const story = document.body.dataset.story;
  if (story) {
    const title = document.body.dataset.title, page = document.body.dataset.page;
    let ready = false;
    const remember = () => {
      if (!ready) return;
      const total = Math.max(1, document.documentElement.scrollHeight - innerHeight);
      state.positions = state.positions || {}; state.positions[story] = Math.min(1, Math.max(0, scrollY / total));
      state.last = { page, title }; save();
    };
    const update = () => {
      const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
      document.querySelector('.reading-progress').style.width = `${Math.min(100, 100 * scrollY / max)}%`;
    };
    window.addEventListener('load', () => {
      if (location.hash === '#resume' && state.positions?.[story]) {
        window.scrollTo({ top: state.positions[story] * (document.documentElement.scrollHeight - innerHeight), behavior: 'instant' });
      }
      ready = true; state.last = { page, title }; save(); update();
    });
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('pagehide', remember);
    document.addEventListener('visibilitychange', () => { if (document.hidden) remember(); });
    const read = document.querySelector('[data-mark-read]');
    const labelRead = () => { const done = !!state.read?.[story]; read.textContent = done ? 'Read ✓' : 'Mark as read'; read.setAttribute('aria-pressed', String(done)); };
    labelRead();
    read.addEventListener('click', () => { state.read = state.read || {}; state.read[story] = !state.read[story]; save(); labelRead(); });
  }
})();
