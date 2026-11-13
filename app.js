"use strict";
(() => {
  const search = document.querySelector('#guide-search');
  if (search) {
    const cards = [...document.querySelectorAll('#guide-grid .guide-card')];
    const filters = [...document.querySelectorAll('[data-category-filter]')];
    let category = '全部';
    const update = () => {
      const query = search.value.trim().toLocaleLowerCase();
      let visible = 0;
      cards.forEach(card => {
        card.hidden = !(category === '全部' || card.dataset.category === category) || !card.dataset.search.toLocaleLowerCase().includes(query);
        if (!card.hidden) visible++;
      });
      document.querySelector('#result-status').textContent = `顯示 ${visible} / ${cards.length} 篇指南`;
      document.querySelector('#empty-state').hidden = visible !== 0;
      filters.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.categoryFilter === category)));
    };
    search.addEventListener('input', update);
    filters.forEach(button => button.addEventListener('click', () => { category = button.dataset.categoryFilter; update(); }));
    document.querySelector('#clear-filters').addEventListener('click', () => { search.value = ''; category = '全部'; update(); search.focus(); });
    update();
  }
  const article = document.querySelector('[data-guide]');
  if (!article) return;
  const key = `trip-ready:v1:${article.dataset.guide}`;
  const boxes = [...article.querySelectorAll('input[type=checkbox]')];
  const ids = new Set(boxes.map(box => box.dataset.checkId));
  const status = article.querySelector('#storage-status');
  let storageAvailable = true;
  try {
    const raw = localStorage.getItem(key);
    const saved = raw === null ? [] : JSON.parse(raw);
    if (!Array.isArray(saved) || saved.some(id => typeof id !== 'string')) throw new Error('Invalid saved checklist');
    boxes.forEach(box => { box.checked = saved.includes(box.dataset.checkId); });
  } catch (_) {
    storageAvailable = false;
    status.textContent = '無法讀取儲存資料；本次仍可勾選，但進度不會保存。';
  }
  const render = () => {
    const count = boxes.filter(box => box.checked).length;
    article.querySelector('#check-count').textContent = `${count} / ${boxes.length}`;
    article.querySelector('#check-progress').value = count;
  };
  const save = () => {
    if (storageAvailable) {
      try { localStorage.setItem(key, JSON.stringify(boxes.filter(box => box.checked).map(box => box.dataset.checkId).filter(id => ids.has(id)))); }
      catch (_) { storageAvailable = false; status.textContent = '無法保存進度；本次仍可勾選，離開後可能不會保留。'; }
    }
    render();
  };
  boxes.forEach(box => box.addEventListener('change', save));
  const reset = article.querySelector('#reset-checklist');
  reset.hidden = false;
  reset.addEventListener('click', () => { boxes.forEach(box => { box.checked = false; }); save(); });
  render();
})();
