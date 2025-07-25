 /* use episode ID so each episode remembers its own spot */
 document.addEventListener('DOMContentLoaded', () => {
    /* grab elements */
    const bar      = document.getElementById('progress-container');
    const barFill  = document.getElementById('progress-bar');
    const tooltip  = document.getElementById('progress-tooltip');
    const playBtn  = document.getElementById('play-btn');
    const tsInput  = document.getElementById('timestamp');
    const comments = document.getElementById('comments-container');
    const toggle   = document.getElementById('toggle-comments');
    if (!bar) return;
  



    /* unique storage key for THIS episode */

    

    // This key is for storing progress bar time elapsed in local storage based; This creates a specific key to a specific episode/ movie
    const STORAGE_KEY = `episode:${bar.dataset.epid}:${location.pathname}`;
  
    /* helpers */
    const duration = Number(bar.dataset.duration) || 0; // this pulls from progress container's displayed number



    /*
    This function create the timestamp display
    */
    const fmt = s => {
      s = Math.round(s);
      const h = String(Math.floor(s/3600)).padStart(2,'0');
      const m = String(Math.floor((s%3600)/60)).padStart(2,'0');
      const c = String(s%60).padStart(2,'0');
      return `${h}:${m}:${c}`;
    };
  
    /* state (pick up saved value) */
    let playing = false; //bool
    let elapsed = Number(localStorage.getItem(STORAGE_KEY)) || 0; // pull elapsed time from local storage, else 0
    let timerId = null;
  
    /* comment‑reveal helper */
    function updateComments()  {
      document.querySelectorAll('.comment').forEach(el => {
        el.style.display = (+el.dataset.secs <= elapsed) ? '' : 'none';
      });
    }
  
    /* render everything */
    function render() {
      const pct = elapsed / duration; //progress percentage
      barFill.style.width = `${Math.min(pct*100,100)}%`; //set the width based on the percentage
  
      const px = pct * bar.clientWidth; //the amount of pixels based on client width * percentage
      tooltip.style.left    = `${px}px`; //css style
      tooltip.textContent   = fmt(elapsed); //the text of the time stamp
      tooltip.style.display = playing ? 'block' : tooltip.style.display; //show based on playing bool
  
      playBtn.textContent = playing ? '❚❚' : '▶';
      if (tsInput) tsInput.value = fmt(elapsed);
  
      updateComments();
      localStorage.setItem(STORAGE_KEY, elapsed);      // <- save here
    }
  
    /* tick every second */
    function tick() {
      elapsed += 1;
      if (elapsed >= duration) { //once the media has be watched completed
        elapsed = duration;
        clearInterval(timerId);
        playing = false;
        localStorage.removeItem(STORAGE_KEY);    // clear the key from local storage
      }
      render();
    }
  
    /* play / pause */
    playBtn.addEventListener('click', () => {
      playing = !playing; // set false
      if (playing) {
        timerId = setInterval(tick, 1000); //update every second
      } else {
        clearInterval(timerId);
      }
      render(); //display the new state of the progress 
    });
  
    /* === bar hover tooltip (only when NOT playing) === */
    bar.addEventListener('mousemove', e => {
      if (playing) return;                  // let auto‑mode handle it
      const rect = bar.getBoundingClientRect();
      const pct  = (e.clientX - rect.left) / rect.width;
      tooltip.style.left    = `${e.clientX - rect.left}px`;
      tooltip.textContent   = fmt(pct * duration);
      tooltip.style.display = 'block';
    });
    

    bar.addEventListener('mouseleave', () => {
      if (!playing) tooltip.style.display = 'none';
    }); //take off fmt display
  
    /* === click (seek) === 
    update the progress bar based on click on the progress bar
    
    */
    bar.addEventListener('click', e => {
      const rect = bar.getBoundingClientRect();
      const pct  = (e.clientX - rect.left) / rect.width;
      elapsed = pct * duration; 
      render();
    });
  
    /* === show / hide comments === */
    if (toggle && comments) {
      toggle.addEventListener('click', () => {
        comments.classList.toggle('hidden');
        toggle.textContent = comments.classList.contains('hidden')
                             ? 'Show Comments' : 'Hide Comments';
      });
    }
  
  
    render();               // initial paint with restored time
  });