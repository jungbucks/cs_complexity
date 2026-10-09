// 수식: data-math가 붙은 요소만 KaTeX로 그린다(코드는 건드리지 않음).
if (window.katex) document.querySelectorAll('[data-math]').forEach(el => {
  try { katex.render(el.dataset.math, el, {throwOnError:true, output:'htmlAndMathml', trust:false}); }
  catch (error) { console.error('Formula failed:', el.dataset.math, error); }
});

// 움직임 줄이기 설정을 따르고, 설정이 바뀌면 바로 반영한다.
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const syncMotion = () => document.documentElement.classList.toggle('js-motion', !reduced.matches);
syncMotion();
reduced.addEventListener?.('change', syncMotion);

// 상단 진행 표시: 스크롤마다 한 프레임에 한 번만 갱신한다.
const progress = document.getElementById('progress');
const progressText = document.getElementById('progress-text');
const progressTrack = progress.parentElement;
let progressQueued = false;
function updateProgress() {
  progressQueued = false;
  const range = document.documentElement.scrollHeight - innerHeight;
  const value = Math.round(Math.max(0, Math.min(100, range > 0 ? scrollY / range * 100 : 0)));
  progress.style.width = value + '%';
  progressText.textContent = `진행 ${value}%`;
  progressTrack.setAttribute('aria-valuenow', value);
}
const queueProgress = () => { if (!progressQueued) { progressQueued = true; requestAnimationFrame(updateProgress); } };
addEventListener('scroll', queueProgress, {passive:true});
new ResizeObserver(queueProgress).observe(document.body);   // 정답·선택 영역을 펼쳐 길이가 바뀔 때도 갱신

// 슬라이드 등장 효과
const slides = [...document.querySelectorAll('.slide')];
const reveals = new IntersectionObserver(entries => entries.forEach(e => {
  if (e.isIntersecting) { e.target.classList.add('seen'); reveals.unobserve(e.target); }
}), {threshold:.03});
slides.forEach(s => reveals.observe(s));

// 키보드로 한 장씩 넘기기: → PageDown Space 다음, ← PageUp 이전.
// (↑↓ 화살표는 일반 스크롤로 남겨 둔다. 펼친 내용이 길면 PageDown/Space는 먼저 그 장 안에서 내려간다.)
// 상단 막대 높이는 CSS 변수(--header) 하나로 정한다.
const HEADER = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header')) || 38;
// 부드러운 스크롤 도중에 키를 연달아 눌러도 빠짐없이 넘어가도록, 가는 중인 목표 장을 기억한다.
let targetIdx = null, targetTimer = 0;
const clearTarget = () => { targetIdx = null; clearTimeout(targetTimer); };
addEventListener('scrollend', clearTarget);
addEventListener('wheel', clearTarget, {passive:true});
addEventListener('touchstart', clearTarget, {passive:true});
function currentSlide() {
  if (targetIdx !== null) return targetIdx;
  let idx = 0;
  slides.forEach((s, i) => { if (s.getBoundingClientRect().top <= HEADER + 4) idx = i; });
  return idx;
}
function goTo(i) {
  targetIdx = Math.max(0, Math.min(slides.length - 1, i));
  clearTimeout(targetTimer);
  targetTimer = setTimeout(clearTarget, 900);   // scrollend를 지원하지 않는 브라우저 대비
  slides[targetIdx].scrollIntoView({behavior: reduced.matches ? 'auto' : 'smooth', block: 'start'});
}
addEventListener('keydown', e => {
  if (e.altKey || e.ctrlKey || e.metaKey || e.defaultPrevented) return;
  const t = e.target;
  if (t.closest?.('input, textarea, select, [contenteditable="true"]')) return;
  const onControl = t.closest?.('button, a, summary');
  const next = e.key === 'ArrowRight' || e.key === 'PageDown' || (e.key === ' ' && !e.shiftKey && !onControl);
  const prev = e.key === 'ArrowLeft' || e.key === 'PageUp' || (e.key === ' ' && e.shiftKey && !onControl);
  if (!next && !prev) return;
  e.preventDefault();
  // 아직 이동 중인 목표 장이 화면보다 길면(펼친 내용), 그 장에 도착한 뒤 장 안에서 내려가도록 이번 입력은 넘긴다.
  if (next && targetIdx !== null && e.key !== 'ArrowRight' && slides[targetIdx].offsetHeight > innerHeight - HEADER + 4) return;
  const i = currentSlide();
  if (next && e.key !== 'ArrowRight' && targetIdx === null) {
    const bottom = slides[i].getBoundingClientRect().bottom;
    if (bottom > innerHeight + 4) { scrollBy({top: innerHeight - HEADER - 80, behavior: reduced.matches ? 'auto' : 'smooth'}); return; }
  }
  if (prev && targetIdx === null && slides[i].getBoundingClientRect().top < HEADER - 4) { goTo(i); return; }   // 긴 장 중간이면 그 장 맨 위로
  goTo(next ? i + 1 : i - 1);
});

// 정답 보기/숨기기. 버튼마다 원래 문구를 기억해 두었다가 되돌린다.
// 정답을 열면 그 슬라이드의 '# ?' 주석과 '?' 칸도 실제 값으로 바뀐다(.revealed).
document.querySelectorAll('.answer-toggle').forEach(button => {
  const showLabel = button.textContent;
  button.addEventListener('click', () => {
    const answer = document.getElementById(button.getAttribute('aria-controls'));
    answer.hidden = !answer.hidden;
    button.setAttribute('aria-expanded', String(!answer.hidden));
    button.textContent = answer.hidden ? showLabel : '다시 숨기기';
    button.closest('.slide')?.classList.toggle('revealed', !answer.hidden);
  });
});

// 코드 복사: 실행 횟수 주석(.cnt)은 빼고 코드만 복사한다.
document.querySelectorAll('.copy-code').forEach(button => button.addEventListener('click', async () => {
  const code = document.querySelector(`#${button.dataset.copy} code`);
  const text = [...code.querySelectorAll('.line .src')].map(src => src.textContent.replace(/\s+$/, '')).join('\n');
  const status = button.parentElement.querySelector('.copy-status');
  try {
    await navigator.clipboard.writeText(text);
    status.textContent = '복사했어요. Colab 칸에 붙여넣으세요.';
  } catch {
    let box = button.parentElement.parentElement.querySelector('.copy-fallback');
    if (!box) {
      box = document.createElement('textarea');
      box.className = 'copy-fallback'; box.readOnly = true;
      box.setAttribute('aria-label', '직접 복사할 Python 코드');
      button.parentElement.after(box);
    }
    box.value = text; box.focus(); box.select();
    status.textContent = '아래 코드가 선택됐어요. Ctrl+C로 복사하세요.';
  }
}));

// 그래프: 처음에는 전체 곡선을 보여 주고, 재생하면 n = 1부터 다시 그린다.
// 축·눈금·격자와 n의 범위(data-max, data-ymax), 곡선 이름(data-labels)은 HTML에 있다.
// 여기에는 함수식과 재생 시간만 둔다. 곡선 색은 .live-value의 글자색(CSS 함수별 색)을 쓴다.
const configs = {
  A:{duration:10000, f:[n=>2*n+2, n=>2*n*n+n+2]},
  D:{duration:10000, f:[n=>n, n=>n*n]},
  B:{duration:12000, f:[()=>1, n=>Math.log2(n), n=>n, n=>n*Math.log2(n)]},
  C:{duration:10000, f:[n=>n*n, n=>n*n*n, n=>2**n]}
};
const DASH = {'fc-1':'2 5','fc-log':'12 4 2 4','fc-n':'none','fc-nlog':'9 6','fc-n2':'none','fc-n3':'4 4','fc-2n':'14 6'};
const X0 = 80, X1 = 780;
const chartControllers = [];
function setPlayLabel(button, symbol, text) {
  button.innerHTML = `<span aria-hidden="true">${symbol}</span> ${text}`;
}
document.querySelectorAll('[data-chart]').forEach(root => {
  const c = {...configs[root.dataset.chart], max:+root.dataset.max, ymax:+root.dataset.ymax, labels:root.dataset.labels.split('|')};
  const svg = root.querySelector('svg'), button = root.querySelector('.play');
  svg.querySelector('.static-curves')?.remove();
  const nNode = root.querySelector('[data-n]');
  const valueBoxes = [...root.querySelectorAll('.live-value')];
  const valueNodes = valueBoxes.map(box => box.querySelector('[data-value]'));
  const colors = valueBoxes.map(box => getComputedStyle(box).color);
  const dashes = valueBoxes.map(box => DASH[[...box.classList].find(k => k.startsWith('fc-'))] || 'none');
  const x = n => X0 + n / c.max * (X1 - X0), y = v => 380 - v / c.ymax * 320;
  const make = (tag, attrs, text) => {
    const e = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    if (text !== undefined) e.textContent = text;
    svg.append(e); return e;
  };
  const plots = c.f.map((f, i) => ({
    path: make('path', {fill:'none', stroke:colors[i], 'stroke-width':4, 'stroke-linecap':'round', 'stroke-dasharray':dashes[i]}),
    dot: make('circle', {r:6, fill:colors[i]}),
    label: make('text', {class:'line-label', fill:colors[i]}, c.labels[i])
  }));
  let lastN = 0;
  const draw = n => {
    if (n === lastN) return;
    lastN = n;
    nNode.textContent = n;
    const occupied = [];
    c.f.forEach((f, i) => {
      const value = f(n), plot = plots[i];
      plot.path.setAttribute('d', Array.from({length:n}, (_, j) => `${j ? 'L' : 'M'}${x(j+1)},${y(f(j+1))}`).join(' '));
      plot.dot.setAttribute('cx', x(n)); plot.dot.setAttribute('cy', y(value));
      let labelY = Math.min(375, Math.max(50, y(value) + 7));
      while (occupied.some(v => Math.abs(v - labelY) < 24)) labelY -= 25;
      occupied.push(labelY);
      plot.label.setAttribute('x', x(n) + 14); plot.label.setAttribute('y', labelY);
      valueNodes[i].textContent = Number(value.toFixed(2)).toLocaleString('en-US');
    });
  };
  let elapsed = c.duration, last = null, running = false, raf;
  const pause = () => {
    running = false; cancelAnimationFrame(raf); last = null;
    button.setAttribute('aria-pressed', 'false');
    if (elapsed >= c.duration) setPlayLabel(button, '↻', '다시 재생'); else setPlayLabel(button, '▶', '계속 재생');
  };
  const frame = time => {
    if (!running) return;
    if (last !== null) elapsed = Math.min(c.duration, elapsed + time - last);
    last = time;
    draw(1 + Math.floor(elapsed / c.duration * (c.max - 1)));
    if (elapsed >= c.duration) { pause(); return; }
    raf = requestAnimationFrame(frame);
  };
  button.setAttribute('aria-pressed', 'false');
  setPlayLabel(button, '▶', '그래프 재생');
  button.addEventListener('click', () => {
    if (running) { pause(); return; }
    if (reduced.matches) { elapsed = c.duration; draw(c.max); setPlayLabel(button, '↻', '다시 재생'); return; }
    if (elapsed >= c.duration) { elapsed = 0; draw(1); }
    running = true; last = null;
    button.setAttribute('aria-pressed', 'true');
    setPlayLabel(button, 'Ⅱ', '일시정지');
    raf = requestAnimationFrame(frame);
  });
  new IntersectionObserver(entries => { if (!entries[0].isIntersecting && running) pause(); }, {threshold:.05}).observe(root);
  const restart = document.createElement('button');
  restart.type = 'button'; restart.className = 'restart'; restart.textContent = '처음(n = 1)으로';
  button.after(restart);
  restart.addEventListener('click', () => { pause(); elapsed = 0; draw(1); setPlayLabel(button, '▶', '그래프 재생'); });
  chartControllers.push({pauseIfRunning: () => { if (running) pause(); }});
  draw(c.max);
});
document.addEventListener('visibilitychange', () => { if (document.hidden) chartControllers.forEach(c => c.pauseIfRunning()); });
updateProgress();
