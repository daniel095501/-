"use strict";
(() => {
  const search = document.querySelector('#wiki-search');
  if (search) {
    const cards = [...document.querySelectorAll('.wiki-card')];
    search.addEventListener('input', () => {
      const query = search.value.trim().toLocaleLowerCase();
      let visible = 0;
      cards.forEach(card => { card.hidden = !card.dataset.search.toLocaleLowerCase().includes(query); if (!card.hidden) visible++; });
      document.querySelector('#wiki-count').textContent = `顯示 ${visible}／${cards.length} 篇知識頁`;
      document.querySelector('#wiki-empty').hidden = visible > 0;
    });
  }
  const slides = [...document.querySelectorAll('.slide')];
  if (!slides.length) return;
  const controls = document.querySelector('.deck-controls');
  const select = document.querySelector('#slide-select');
  const prev = document.querySelector('#slide-prev');
  const next = document.querySelector('#slide-next');
  let current = 0;
  const show = (index, scroll = true) => {
    current = Math.min(slides.length - 1, Math.max(0, index));
    slides.forEach((slide,i) => { slide.hidden = i !== current; });
    select.value = String(current);
    prev.disabled = current === 0;
    next.disabled = current === slides.length - 1;
    document.querySelector('#slide-status').textContent = `第${current+1}頁，共${slides.length}頁：${slides[current].querySelector('h2').textContent}`;
    try { history.replaceState(null, '', '#'+slides[current].id); } catch (_) { /* File preview still permits reading and navigation. */ }
    if (scroll) window.scrollTo({top:0,behavior:'instant'});
  };
  const fromHash = () => { const i = slides.findIndex(slide => '#'+slide.id === location.hash); show(i < 0 ? 0 : i, false); };
  controls.hidden = false;
  prev.addEventListener('click',()=>show(current-1));
  next.addEventListener('click',()=>show(current+1));
  select.addEventListener('change',()=>show(Number(select.value)));
  window.addEventListener('hashchange',fromHash);
  document.addEventListener('keydown',event=>{
    if (event.altKey || event.ctrlKey || event.metaKey || event.target.closest('input,textarea,select,[contenteditable=true]')) return;
    const movement = {ArrowRight:current+1,PageDown:current+1,ArrowLeft:current-1,PageUp:current-1,Home:0,End:slides.length-1};
    if (Object.prototype.hasOwnProperty.call(movement,event.key)) { event.preventDefault(); show(movement[event.key]); }
  });
  document.querySelectorAll('.quiz').forEach(quiz=>{
    const button=quiz.querySelector('.check-answer');button.hidden=false;
    button.addEventListener('click',()=>{
      const selected=quiz.querySelector('input:checked');
      const feedback=quiz.querySelector('.quiz-feedback');
      if (!selected) { quiz.dataset.result='empty'; feedback.textContent='請先選一個答案，再確認。'; return; }
      const correct=selected.value===quiz.dataset.answer;
      quiz.dataset.result=correct?'correct':'retry';
      feedback.textContent=(correct?'判斷正確。':'再核對一次。')+quiz.dataset.feedback;
    });
  });
  fromHash();
})();
