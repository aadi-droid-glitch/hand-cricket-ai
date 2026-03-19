// game.js — Hand Cricket AI frontend logic

const API = '';   // same origin
let state = {
  playerName  : '',
  tossCall    : '',
  firstBatter : '',
  innings     : 1,
  score       : 0,
  ballCount   : 0,
  target      : null,
  innings1Runs: 0,
  ballLog     : [],
  waitingNext : false,
};

// ── Helpers ──────────────────────────────────────────────────────────────

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function post(url, body) {
  return fetch(url, {
    method : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body   : JSON.stringify(body),
  }).then(r => r.json());
}

function buildNumberGrid(containerId, handler, disabled = false) {
  const grid = document.getElementById(containerId);
  grid.innerHTML = '';
  for (let i = 1; i <= 10; i++) {
    const btn = document.createElement('button');
    btn.className   = 'num-btn';
    btn.textContent = i;
    btn.disabled    = disabled;
    btn.onclick     = () => handler(i, btn);
    grid.appendChild(btn);
  }
}

function disableGrid(containerId) {
  document.querySelectorAll(`#${containerId} .num-btn`)
    .forEach(b => b.disabled = true);
}

function addBallChip(runs, out) {
  const log  = document.getElementById('ball-log');
  const chip = document.createElement('div');
  chip.className = `ball-chip ${out ? 'out' : 'scored'}`;
  chip.textContent = out ? 'OUT' : `+${runs}`;
  log.appendChild(chip);
  log.scrollLeft = log.scrollWidth;
}

function updateScoreboard() {
  const sb = document.getElementById('scoreboard');
  const humanBatting = (
    (state.innings === 1 && state.firstBatter === state.playerName) ||
    (state.innings === 2 && state.firstBatter !== state.playerName)
  );
  const targetLine = state.target
    ? `<div class="score-label">TARGET ${state.target}</div>`
    : '';

  if (humanBatting) {
    sb.innerHTML = `
      <div class="score-box active-batter">
        <div class="score-name">${state.playerName}</div>
        <div class="score-runs">${state.score}</div>
        <div class="score-label">BATTING</div>
        ${targetLine}
      </div>
      <div class="score-box">
        <div class="score-name">AI</div>
        <div class="score-runs">—</div>
        <div class="score-label">BOWLING</div>
      </div>`;
  } else {
    const needed = state.target ? state.target - state.score : null;
    sb.innerHTML = `
      <div class="score-box">
        <div class="score-name">${state.playerName}</div>
        <div class="score-runs">${state.innings1Runs}</div>
        <div class="score-label">SET TARGET ${state.target}</div>
      </div>
      <div class="score-box active-batter">
        <div class="score-name">AI</div>
        <div class="score-runs">${state.score}</div>
        <div class="score-label">BATTING${needed ? ' · NEEDS ' + needed : ''}</div>
      </div>`;
  }
}

// ── Screen 1: Login ───────────────────────────────────────────────────────

async function loadPlayer() {
  const input = document.getElementById('player-name-input');
  const name  = input.value.trim();
  if (!name) return;

  const data = await post('/api/player/load', { name });
  state.playerName = data.name;

  // Build profile strip
  const strip = document.getElementById('profile-strip');
  strip.innerHTML = `
    <div class="profile-stat">
      <div class="val">${data.matches_played}</div>
      <div class="lbl">MATCHES</div>
    </div>
    <div class="profile-stat">
      <div class="val">${data.matches_won}</div>
      <div class="lbl">WINS</div>
    </div>
    <div class="profile-stat">
      <div class="val">${data.history_balls}</div>
      <div class="lbl">BALLS FACED</div>
    </div>
    <div class="profile-stat">
      <div class="val">${data.favourite !== '?' ? data.favourite : '—'}</div>
      <div class="lbl">FAVOURITE NO.</div>
    </div>`;

  if (data.predictability >= 0) {
    document.getElementById('pred-warning').style.display = 'block';
    document.getElementById('pred-warning').textContent =
      `👁  AI HAS MODELLED ${data.predictability}% OF YOUR BEHAVIOUR`;
  }

  showScreen('screen-lobby');
}

// ── Screen 3: Toss ────────────────────────────────────────────────────────

function startToss() {
  showScreen('screen-toss');
}

function tossPick(call) {
  state.tossCall = call;
  document.getElementById('toss-call-display').textContent =
    `YOU CALLED: ${call.toUpperCase()} — NOW REVEAL YOUR NUMBER`;
  buildNumberGrid('toss-number-grid', tossReveal);
  showScreen('screen-toss-number');
}

async function tossReveal(num) {
  disableGrid('toss-number-grid');

  const data = await post('/api/toss/reveal', {
    player_name: state.playerName,
    call       : state.tossCall,
    player_num : num,
  });

  const winner = data.winner;
  const youWon = winner === state.playerName;

  const display = document.getElementById('toss-result-display');
  display.innerHTML = `
    <span style="color:var(--green)">${state.playerName}</span> chose <b>${data.player_num}</b> &nbsp;·&nbsp;
    <span style="color:var(--amber)">AI</span> chose <b>${data.ai_num}</b><br/>
    SUM = ${data.total} (${data.result.toUpperCase()})<br/>
    YOU CALLED ${state.tossCall.toUpperCase()} →
    <span style="color:${youWon ? 'var(--green)' : 'var(--red)'}">
      ${youWon ? 'CORRECT' : 'WRONG'}
    </span><br/><br/>
    <span style="font-family:var(--font-disp); font-size:1.4rem; letter-spacing:3px; color:${youWon ? 'var(--green)' : 'var(--amber)'}">
      ${winner.toUpperCase()} WINS THE TOSS
    </span>`;

  const choiceDiv = document.getElementById('bat-bowl-choice');
  if (youWon) {
    choiceDiv.innerHTML = `
      <p style="font-size:0.75rem; letter-spacing:2px; color:var(--muted); margin-bottom:1rem;">YOUR CALL — BAT OR BOWL?</p>
      <div class="toss-choice">
        <button class="btn" onclick="selectBatBowl('bat')">BAT</button>
        <button class="btn btn-amber" onclick="selectBatBowl('bowl')">BOWL</button>
      </div>`;
  } else {
    // AI decides randomly
    const aiChoice = Math.random() < 0.5 ? 'bat' : 'bowl';
    choiceDiv.innerHTML = `
      <p style="color:var(--amber); font-size:0.8rem; letter-spacing:2px; margin-bottom:1rem;">
        AI CHOSE TO ${aiChoice.toUpperCase()}
      </p>
      <button class="btn" onclick="selectBatBowl('${aiChoice === 'bat' ? 'bowl' : 'bat'}', true)">
        CONTINUE
      </button>`;
  }

  showScreen('screen-toss-result');
}

async function selectBatBowl(choice, aiChose = false) {
  const finalChoice = aiChose ? (choice === 'bat' ? 'bowl' : 'bat') : choice;
  const data = await post('/api/toss/choice', {
    player_name: state.playerName,
    choice     : finalChoice,
  });

  state.firstBatter = data.first_batter;
  state.innings     = 1;
  state.score       = 0;
  state.ballCount   = 0;
  state.target      = null;
  state.ballLog     = [];
  document.getElementById('ball-log').innerHTML = '';

  startInnings(1);
}

// ── Game screen ───────────────────────────────────────────────────────────

function startInnings(num) {
  state.innings   = num;
  state.score     = 0;
  state.ballCount = 0;
  state.waitingNext = false;

  const humanBatting = (
    (num === 1 && state.firstBatter === state.playerName) ||
    (num === 2 && state.firstBatter !== state.playerName)
  );

  document.getElementById('innings-label').textContent = `INNINGS ${num}`;
  document.getElementById('pick-label').textContent =
    humanBatting ? 'PICK YOUR NUMBER' : 'PICK YOUR BOWL NUMBER';
  document.getElementById('ball-log').innerHTML = '';
  document.getElementById('reveal-box').style.display = 'none';
  document.getElementById('result-banner').style.display = 'none';

  updateScoreboard();
  buildNumberGrid('game-number-grid', handleBall);
  setStatus(humanBatting
    ? 'YOU ARE BATTING — PICK A NUMBER'
    : 'YOU ARE BOWLING — PICK A NUMBER TO BOWL');

  showScreen('screen-game');
}

function startInnings2() {
  startInnings(2);
}

function setStatus(msg, highlight = false) {
  const el = document.getElementById('game-status');
  el.textContent = msg;
  el.className = `status-line${highlight ? ' highlight' : ''}`;
}

async function handleBall(num, btn) {
  if (state.waitingNext) return;
  disableGrid('game-number-grid');
  btn.classList.add('selected');

  const data = await post('/api/ball/play', {
    player_name: state.playerName,
    number     : num,
  });

  state.ballCount = data.ball_num;
  state.score     = data.total;

  const humanBatting = data.human_is_batting;
  const batNum = data.batter_num;
  const bowNum = data.bowler_num;

  // Show reveal
  const revealBox = document.getElementById('reveal-box');
  revealBox.style.display = 'flex';
  document.getElementById('reveal-num-left').textContent  = humanBatting ? batNum : bowNum;
  document.getElementById('reveal-num-right').textContent = humanBatting ? bowNum : batNum;
  document.getElementById('reveal-label-left').textContent  = humanBatting ? state.playerName.toUpperCase() : 'YOU (BOWL)';
  document.getElementById('reveal-label-right').textContent = humanBatting ? 'AI (BOWL)' : 'AI (BAT)';

  // Result banner
  const banner = document.getElementById('result-banner');
  if (data.out) {
    banner.className = 'result-banner out-banner';
    banner.textContent = `💥 OUT — BOTH CHOSE ${batNum}`;
    banner.style.display = 'block';
    document.getElementById('reveal-num-left').classList.add('out');
    document.getElementById('reveal-num-right').classList.add('out');
  } else {
    banner.className = 'result-banner safe-banner';
    banner.textContent = humanBatting
      ? `+${data.runs_this_ball} RUNS`
      : `AI SCORES +${data.runs_this_ball}`;
    banner.style.display = 'block';
  }

  addBallChip(data.runs_this_ball, data.out);
  updateScoreboard();

  // ── Innings or match over ────────────────────────────────────────────
  if (data.innings_over) {
    if (data.match_over) {
      setTimeout(() => showMatchOver(data), 1200);
    } else {
      // Innings 1 over — show break screen
      state.innings1Runs = data.innings1_runs;
      state.target       = data.target;
      setTimeout(() => {
        const msg = document.getElementById('break-message');
        msg.innerHTML = `
          <span style="color:var(--green)">${state.firstBatter.toUpperCase()}</span>
          SCORED <span style="font-family:var(--font-disp); font-size:1.8rem; color:var(--green)">${data.innings1_runs}</span> RUNS<br/>
          <span style="color:var(--amber)">${state.firstBatter === state.playerName ? 'AI' : state.playerName}</span>
          NEEDS <span style="font-family:var(--font-disp); font-size:1.8rem; color:var(--amber)">${data.target}</span> TO WIN`;
        showScreen('screen-break');
      }, 1200);
    }
  } else {
    // Continue — re-enable after short delay
    state.waitingNext = true;
    setTimeout(() => {
      state.waitingNext = false;
      document.getElementById('reveal-num-left').classList.remove('out');
      document.getElementById('reveal-num-right').classList.remove('out');
      banner.style.display = 'none';
      buildNumberGrid('game-number-grid', handleBall);
      const humanBat = (
        (state.innings === 1 && state.firstBatter === state.playerName) ||
        (state.innings === 2 && state.firstBatter !== state.playerName)
      );
      if (state.target) {
        const needed = state.target - state.score;
        setStatus(`SCORE: ${state.score} · NEED ${needed} MORE`, needed <= 10);
      }
    }, 900);
  }
}

// ── Match over ────────────────────────────────────────────────────────────

function showMatchOver(data) {
  const youWon = data.winner === state.playerName;
  const wd = document.getElementById('winner-display');
  wd.innerHTML = `
    <div class="trophy">${youWon ? '🏆' : '🤖'}</div>
    <h2>${data.winner.toUpperCase()} WINS</h2>
    <p>${state.playerName.toUpperCase()}: ${data.innings1_runs ?? data.innings2_runs} RUNS &nbsp;·&nbsp; AI: ${data.innings2_runs ?? data.innings1_runs} RUNS</p>`;

  if (data.insights) renderInsights(data.insights);

  showScreen('screen-over');
}

function renderInsights(ins) {
  if (ins.message) return;

  const freq  = ins.number_frequency || {};
  const total = Object.values(freq).reduce((a, b) => a + b, 0) || 1;

  // Stat cards
  const grid = document.getElementById('insights-grid');
  grid.innerHTML = `
    <div class="insight-stat">
      <div class="insight-label">FAVOURITE NUMBER</div>
      <div class="insight-value">${ins.favourite_number ?? '—'}</div>
    </div>
    <div class="insight-stat">
      <div class="insight-label">LEAST USED</div>
      <div class="insight-value amber">${ins.least_used_number ?? '—'}</div>
    </div>
    <div class="insight-stat">
      <div class="insight-label">FIRST BALL TENDENCY</div>
      <div class="insight-value" style="font-size:1rem; padding-top:0.5rem;">${ins.first_ball_tendency ?? '—'}</div>
    </div>
    <div class="insight-stat">
      <div class="insight-label">PREDICTABILITY</div>
      <div class="insight-value ${ins.predictability?.includes('hard') ? '' : 'red'}" style="font-size:0.9rem; padding-top:0.3rem;">${ins.predictability ?? '—'}</div>
    </div>`;

  // Distribution bars
  const bars = document.getElementById('dist-bars');
  bars.innerHTML = '';
  for (let n = 1; n <= 10; n++) {
    const count = freq[n] ?? 0;
    const pct   = (count / total * 100).toFixed(1);
    const row   = document.createElement('div');
    row.className = 'dist-bar-row';
    row.innerHTML = `
      <span class="dist-num">${n}</span>
      <div class="dist-bar-bg">
        <div class="dist-bar-fill" style="width:${pct}%"></div>
      </div>
      <span class="dist-pct">${pct}%</span>`;
    bars.appendChild(row);
  }
}

// ── Navigation ────────────────────────────────────────────────────────────

function playAgain() {
  state.score     = 0;
  state.ballCount = 0;
  state.target    = null;
  state.ballLog   = [];
  startToss();
}

function goLobby() {
  loadPlayer_silent();
}

async function loadPlayer_silent() {
  const data = await post('/api/player/load', { name: state.playerName });
  const strip = document.getElementById('profile-strip');
  strip.innerHTML = `
    <div class="profile-stat"><div class="val">${data.matches_played}</div><div class="lbl">MATCHES</div></div>
    <div class="profile-stat"><div class="val">${data.matches_won}</div><div class="lbl">WINS</div></div>
    <div class="profile-stat"><div class="val">${data.history_balls}</div><div class="lbl">BALLS FACED</div></div>
    <div class="profile-stat"><div class="val">${data.favourite !== '?' ? data.favourite : '—'}</div><div class="lbl">FAVOURITE NO.</div></div>`;
  if (data.predictability >= 0) {
    document.getElementById('pred-warning').style.display = 'block';
    document.getElementById('pred-warning').textContent =
      `👁  AI HAS MODELLED ${data.predictability}% OF YOUR BEHAVIOUR`;
  }
  showScreen('screen-lobby');
}

// Enter key on login
document.getElementById('player-name-input')
  .addEventListener('keydown', e => { if (e.key === 'Enter') loadPlayer(); });
