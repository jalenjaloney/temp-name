const input = document.getElementById('search-input');
const clearBtn = document.querySelector('.search__clear');
const resultsEl = document.getElementById('search-results');

let controller = null;
let activeIndex = -1;
let items = [];

// ---- helpers --------------------------------------------------

function debounce(fn, delay = 250) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), delay);
  };
}

function escapeHtml(str) {
  return str.replace(/[&<>"']/g, s => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[s]));
}


// Highlights the specific matching string in the search
function highlight(text, q) {
  if (!q) return escapeHtml(text);
  const re = new RegExp(`(${q.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\$&')})`, 'ig');
  return escapeHtml(text).replace(re, '<span class="match">$1</span>');
}

function openDropdown() {
  resultsEl.hidden = false;
  input.setAttribute('aria-expanded', 'true');
}
function closeDropdown() {
  resultsEl.hidden = true;
  input.setAttribute('aria-expanded', 'false');
  activeIndex = -1;
  input.removeAttribute('aria-activedescendant');
}
// show the list of matching media
function renderResults(list, q) {
    items = list;
    if (!list.length) {
      resultsEl.innerHTML = `<li class="no-results" role="option" aria-disabled="true">No results</li>`;
      openDropdown();
      return;
    }
    
    resultsEl.innerHTML = list.map((it, i) => `
        <li id="search-opt-${i}" role="option" aria-selected="${i === activeIndex}" class="search-result-item">
            <div class="search-content">
            <div class="search-text">
                ${highlight(it.title ?? '', q)}
                ${it.description ? `<small class="search-desc">${escapeHtml(it.description.slice(0, 60))}...</small>` : ''}
            </div>
            ${it.poster_url ? `<img class="search-poster" src="${it.poster_url}" alt="${it.title}"/>` : ''}
            </div>
        </li>
    `).join('');
    openDropdown();
  }

function setActive(index) {
  const options = [...resultsEl.querySelectorAll('li[role="option"]')];
  if (!options.length) return;
  // clamp
  if (index < 0) index = options.length - 1;
  if (index >= options.length) index = 0;

  // clear old
  options.forEach(opt => opt.setAttribute('aria-selected', 'false'));

  const el = options[index];
  el.setAttribute('aria-selected', 'true');
  el.scrollIntoView({ block: 'nearest' });

  activeIndex = index;
  input.setAttribute('aria-activedescendant', el.id);
}

function chooseActive() {
  if (activeIndex < 0 || activeIndex >= items.length) return;
  choose(items[activeIndex]);
}

function choose(item) {
    input.value = (item.title ?? '').trim();
    clearBtn.hidden = input.value.length === 0;
    closeDropdown();
    
    // Navigate to the appropriate page based on media type
    if (item.media_type === 'movie') {
      window.location.href = `/movie/${item.id}`;
    } else if (item.media_type === 'tv') {
      window.location.href = `/media/${item.id}`;
    }
    
    console.log('Chosen:', item);
  }

// ---- events ---------------------------------------------------

input.addEventListener('input', () => {
  const q = input.value.trim();
  clearBtn.hidden = q.length === 0;
  if (!q) {
    closeDropdown();
    return;
  }
  doSearch(q);
});

input.addEventListener('keydown', (e) => {
  const optionsExist = !resultsEl.hidden && resultsEl.querySelector('[role="option"]');
  if (!optionsExist) return;

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault();
      setActive(activeIndex + 1);
      break;
    case 'ArrowUp':
      e.preventDefault();
      setActive(activeIndex - 1);
      break;
    case 'Enter':
      e.preventDefault();
      chooseActive();
      break;
    case 'Escape':
      closeDropdown();
      break;
  }
});

clearBtn.addEventListener('click', () => {
  input.value = '';
  clearBtn.hidden = true;
  closeDropdown();
  input.focus();
});

resultsEl.addEventListener('mousedown', (e) => {
  // mousedown so we can pick before blur fires
  const li = e.target.closest('li[role="option"]');
  if (!li) return;
  const idx = [...resultsEl.children].indexOf(li);
  if (idx >= 0) choose(items[idx]);
});

document.addEventListener('click', (e) => {
  if (!e.target.closest('.search')) {
    closeDropdown();
  }
});

// ---- network --------------------------------------------------

const doSearch = debounce(async (q) => {
    if (controller) controller.abort();
    controller = new AbortController();
  
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=10`, {
        signal: controller.signal
      });
      if (!res.ok) return;
      const data = await res.json(); // returns [{id, title, description, media_type, poster_url}, ...]
      activeIndex = -1;
      renderResults(data, q);
    } catch (e) {
      if (e.name !== 'AbortError') console.error(e);
    }
  }, 250);
