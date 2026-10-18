'use strict';
const cards = [...document.querySelectorAll('.option')];
const search = document.querySelector('#search');
const kind = document.querySelector('#kind');
const status = document.querySelector('#status');
const only = document.querySelector('#only-shortlist');
const filters = document.querySelector('.filters');
function update() {
  const words = search.value.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
  let visible = 0;
  let selected = 0;
  for (const card of cards) {
    const checked = card.querySelector('input').checked;
    selected += Number(checked);
    const matches = words.every(word => card.textContent.toLocaleLowerCase().includes(word)) &&
      (!kind.value || card.dataset.kind === kind.value) &&
      (!status.value || card.dataset.status === status.value) && (!only.checked || checked);
    card.hidden = !matches;
    visible += Number(matches);
  }
  document.querySelector('#result-count').textContent = `${visible} of ${cards.length} options · ${selected} shortlisted · Selections reset on reload`;
  document.querySelector('#no-results').hidden = visible > 0 || cards.length === 0;
}
filters.hidden = false;
filters.addEventListener('input', update);
for (const card of cards) card.querySelector('input').addEventListener('change', update);
document.querySelector('#reset').addEventListener('click', () => {
  search.value = kind.value = status.value = '';
  only.checked = false;
  update();
});
// Itinerary links reveal an option even when filters previously hid it.
function revealOption() {
  const card = cards.find(item => `#${item.id}` === location.hash);
  if (!card) return;
  search.value = kind.value = status.value = '';
  only.checked = false;
  update();
  card.querySelector('details').open = true;
  card.scrollIntoView({block: 'start'});
}
window.addEventListener('hashchange', revealOption);
document.querySelector('.timeline').addEventListener('click', event => {
  if (event.target.closest('a')?.getAttribute('href') === location.hash) revealOption();
});
update();
revealOption();
