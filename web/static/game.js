// game.js — Hand Cricket AI — Phase 4 + toss bug fix

const API = '';
let state = {
  mode        : 'ai',
  playerName  : '',
  player2Name : '',
  tossCall    : '',
  firstBatter : '',
  innings     : 1,
  score       : 0,
  ballCount   : 0,
  target      : null,
  innings1Runs: 0,
  waitingNext : false,
  pvpPhase    : 'p1',
  pvpP1Num    : 0,
  pvpP2Num    : 0,
  pvpScore    : 0,
  pvpBallCount: 0,
  pvpTossP1Num: 0,
};

// ── Helpers ───────────────────────────────────────────────────────────────

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  window.scrollTo(0, 0);
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

function disableGrid(id) {
  document.querySelectorAll(`#${id} .num-btn`).forEach(b => b.disabled = true);
}

function addBallChip(logId, runs, out) {
  const log  = document.getElementById(logId);
  const chip = document.createElement('div');
  chip.className   = `ball-chip ${out ? 'out' : 'scored'}`;
  chip.textContent = out ? 'OUT' : `+${runs}`;
  log.appendChild(chip);
  log.scrollLeft = log.scrollWidth;
}

// ── Screen 1: Mode select + login ─────────────────────────────────────────

function setMode(mode) {
  state.mode = mode;
  const p1   = document.getElementById('player-name-input').value.trim();
  if (!p1) {
    document.getElementById('player-name-input').focus();
    return;
  }
  if (mode === 'pvp') {
    document.getElementById('p2-input-wrap').style.display = 'block';
    const p2 = document.getElementById('player2-name-input').value.trim();
    if (p2) loadPlayers();
    else document.getElementById('player2-name-input').focus();
  } else {
    loadPlayers();
  }
}

async function loadPlayers() {
  const p1 = document.getElementById('player-name-input').value.trim();
  const p2 = state.mode === 'pvp'
    ? document.getElementById('player2-name-input').value.trim()
    : 'AI';

  if (!p1 || (state.mode === 'pvp' && !p2)) return;

  state.playerName  = p1;
  state.player2Name = state.mode === 'pvp' ? p2 : 'AI';

  const data = await post('/api/player/load', { name: p1 });
  state.playerName = data.name;

  const lobbyTitle = document.getElementById('lobby-title');
  const strip      = document.getElementById('profile-strip');

  if (state.mode === 'pvp') {
    const p2Title = p2.trim().replace(/\b\w/g, c => c.toUpperCase());
    state.player2Name = p2Title;
    lobbyTitle.textContent = `${data.name}  VS  ${p2Title}`;
    strip.innerHTML = `
      <div class="profile-stat"><div class="val" style="color:var(--green)">${data.name}</div><div class="lbl">PLAYER 1</div></div>
      <div class="profile-stat"><div class="val" style="color:var(--blue)">${p2Title}</div><div class="lbl">PLAYER 2</div></div>
      <div class="profile-stat"><div class="val">${data.matches_played}</div><div class="lbl">P1 MATCHES</div></div>`;
  } else {
    lobbyTitle.textContent = 'PLAYER PROFILE';
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
  }
  showScreen('screen-lobby');
}

// ── Toss ──────────────────────────────────────────────────────────────────

function startToss() {
  const prompt = document.getElementById('toss-call-prompt');
  prompt.textContent = state.mode === 'pvp'
    ? `${state.playerName.toUpperCase()} — CALL ODD OR EVEN`
    : 'CALL ODD OR EVEN';
  showScreen('screen-toss');
}

function tossPick(call) {
  state.tossCall = call;

  // In PvP: P1 enters number first, then P2 enters number, then reveal
  // In AI: P1 enters number, AI picks automatically
  const label = state.mode === 'pvp'
    ? `${state.playerName.toUpperCase()} CALLED: ${call.toUpperCase()} — ${state.playerName.toUpperCase()}, ENTER YOUR TOSS NUMBER`
    : `YOU CALLED: ${call.toUpperCase()} — REVEAL YOUR NUMBER`;

  document.getElementById('toss-call-display').textContent = label;
  buildNumberGrid('toss-number-grid', tossP1Number);
  showScreen('screen-toss-number');
}

function tossP1Number(num, btn) {
  disableGrid('toss-number-grid');
  btn.classList.add('selected');

  if (state.mode === 'pvp') {
    // Save P1 number, now ask P2
    state.pvpTossP1Num = num;
    setTimeout(() => {
      document.getElementById('toss-call-display').textContent =
        `${state.player2Name.toUpperCase()} — ENTER YOUR TOSS NUMBER (other player, look away!)`;
      buildNumberGrid('toss-number-grid', tossP2Number);
    }, 400);
  } else {
    // AI mode — reveal immediately
    tossRevealAI(num);
  }
}

function tossP2Number(num, btn) {
  disableGrid('toss-number-grid');
  btn.classList.add('selected-p2');
  tossRevealPvP(state.pvpTossP1Num, num);
}

async function tossRevealAI(p1num) {
  const data = await post('/api/toss/reveal', {
    player_name: state.playerName,
    call       : state.tossCall,
    player_num : p1num,
  });

  const youWon  = data.winner === state.playerName;
  const display = document.getElementById('toss-result-display');

  display.innerHTML = `
    <span style="color:var(--green)">${state.playerName.toUpperCase()}</span> chose <b>${data.player_num}</b> &nbsp;·&nbsp;
    <span style="color:var(--amber)">AI</span> chose <b>${data.ai_num}</b><br/>
    SUM = ${data.total} (${data.result.toUpperCase()})<br/>
    ${state.playerName.toUpperCase()} CALLED ${state.tossCall.toUpperCase()} →
    <span style="color:${youWon ? 'var(--green)' : 'var(--red)'}">
      ${youWon ? 'CORRECT' : 'WRONG'}
    </span><br/><br/>
    <span style="font-family:var(--font-disp);font-size:1.4rem;letter-spacing:3px;color:${youWon ? 'var(--green)' : 'var(--amber)'}">
      ${data.winner.toUpperCase()} WINS THE TOSS
    </span>`;

  const choiceDiv = document.getElementById('bat-bowl-choice');
  if (youWon) {
    choiceDiv.innerHTML = `
      <p style="font-size:0.75rem;letter-spacing:2px;color:var(--muted);margin-bottom:1rem;">YOUR CALL — BAT OR BOWL?</p>
      <div class="toss-choice">
        <button class="btn" onclick="selectBatBowl('bat', true)">BAT</button>
        <button class="btn btn-amber" onclick="selectBatBowl('bowl', true)">BOWL</button>
      </div>`;
  } else {
    const aiChoice = Math.random() < 0.5 ? 'bat' : 'bowl';
    choiceDiv.innerHTML = `
      <p style="color:var(--amber);font-size:0.8rem;letter-spacing:2px;margin-bottom:1rem;">
        AI CHOSE TO ${aiChoice.toUpperCase()}
      </p>
      <button class="btn" onclick="selectBatBowl('${aiChoice === 'bat' ? 'bowl' : 'bat'}', false)">CONTINUE</button>`;
  }
  showScreen('screen-toss-result');
}

function tossRevealPvP(p1num, p2num) {
  const total      = p1num + p2num;
  const result     = total % 2 !== 0 ? 'odd' : 'even';
  const callerWins = result === state.tossCall.toLowerCase();
  const winner     = callerWins ? state.playerName : state.player2Name;
  const loser      = callerWins ? state.player2Name : state.playerName;

  const display = document.getElementById('toss-result-display');
  display.innerHTML = `
    <span style="color:var(--green)">${state.playerName.toUpperCase()}</span> chose <b>${p1num}</b> &nbsp;·&nbsp;
    <span style="color:var(--blue)">${state.player2Name.toUpperCase()}</span> chose <b>${p2num}</b><br/>
    SUM = ${total} (${result.toUpperCase()})<br/>
    ${state.playerName.toUpperCase()} CALLED ${state.tossCall.toUpperCase()} →
    <span style="color:${callerWins ? 'var(--green)' : 'var(--red)'}">
      ${callerWins ? 'CORRECT' : 'WRONG'}
    </span><br/><br/>
    <span style="font-family:var(--font-disp);font-size:1.4rem;letter-spacing:3px;color:var(--green)">
      ${winner.toUpperCase()} WINS THE TOSS
    </span>`;

  const choiceDiv = document.getElementById('bat-bowl-choice');
  choiceDiv.innerHTML = `
    <p style="font-size:0.75rem;letter-spacing:2px;color:var(--muted);margin-bottom:1rem;">
      ${winner.toUpperCase()} — BAT OR BOWL?
    </p>
    <div class="toss-choice">
      <button class="btn" onclick="selectPvPBatBowl('bat','${winner}')">BAT</button>
      <button class="btn btn-amber" onclick="selectPvPBatBowl('bowl','${winner}')">BOWL</button>
    </div>`;

  showScreen('screen-toss-result');
}

async function selectBatBowl(choice, winnerIsP1) {
  const firstBatter = winnerIsP1
    ? (choice === 'bat' ? state.playerName : 'AI')
    : (choice === 'bat' ? 'AI' : state.playerName);

  await post('/api/toss/choice', {
    player_name: state.playerName,
    choice     : firstBatter === state.playerName ? 'bat' : 'bowl',
  });

  state.firstBatter = firstBatter;
  state.innings     = 1;
  state.score       = 0;
  state.ballCount   = 0;
  state.target      = null;
  startInnings(1);
}

function selectPvPBatBowl(choice, winner) {
  const firstBatter = choice === 'bat' ? winner
    : (winner === state.playerName ? state.player2Name : state.playerName);

  state.firstBatter = firstBatter;
  state.innings     = 1;
  state.target      = null;
  startPvPInnings(1);
}

// ── AI Mode game ──────────────────────────────────────────────────────────

function startInnings(num) {
  state.innings     = num;
  state.score       = 0;
  state.ballCount   = 0;
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
  showScreen('screen-game');
}

function startInnings2() {
  if (state.mode === 'pvp') startPvPInnings(2);
  else startInnings(2);
}

function updateScoreboard() {
  const sb = document.getElementById('scoreboard');
  const humanBatting = (
    (state.innings === 1 && state.firstBatter === state.playerName) ||
    (state.innings === 2 && state.firstBatter !== state.playerName)
  );
  const targetLine = state.target
    ? `<div class="score-label">TARGET ${state.target}</div>` : '';

  if (humanBatting) {
    sb.innerHTML = `
      <div class="score-box active-batter">
        <div class="score-name">${state.playerName}</div>
        <div class="score-runs">${state.score}</div>
        <div class="score-label">BATTING</div>${targetLine}
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
        <div class="score-label">SET ${state.target}</div>
      </div>
      <div class="score-box active-batter">
        <div class="score-name">AI</div>
        <div class="score-runs">${state.score}</div>
        <div class="score-label">BATTING${needed ? ' · NEEDS ' + needed : ''}</div>
      </div>`;
  }
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

  const revealBox = document.getElementById('reveal-box');
  revealBox.style.display = 'flex';
  document.getElementById('reveal-num-left').textContent   = humanBatting ? batNum : bowNum;
  document.getElementById('reveal-num-right').textContent  = humanBatting ? bowNum : batNum;
  document.getElementById('reveal-label-left').textContent  = humanBatting ? state.playerName.toUpperCase() : 'YOU (BOWL)';
  document.getElementById('reveal-label-right').textContent = humanBatting ? 'AI (BOWL)' : 'AI (BAT)';

  const banner = document.getElementById('result-banner');
  if (data.out) {
    banner.className = 'result-banner out-banner';
    banner.textContent = `💥 OUT — BOTH CHOSE ${batNum}`;
    banner.style.display = 'block';
    document.getElementById('reveal-num-left').classList.add('out-color');
    document.getElementById('reveal-num-right').classList.add('out-color');
  } else {
    banner.className = 'result-banner safe-banner';
    banner.textContent = humanBatting ? `+${data.runs_this_ball} RUNS` : `AI SCORES +${data.runs_this_ball}`;
    banner.style.display = 'block';
  }

  addBallChip('ball-log', data.runs_this_ball, data.out);
  updateScoreboard();

  if (data.innings_over) {
    if (data.match_over) {
      setTimeout(() => showMatchOver(data), 1200);
    } else {
      state.innings1Runs = data.innings1_runs;
      state.target       = data.target;
      setTimeout(() => {
        const batter = state.firstBatter;
        const chaser = batter === state.playerName ? 'AI' : state.playerName;
        document.getElementById('break-message').innerHTML = `
          <span style="color:var(--green)">${batter.toUpperCase()}</span>
          SCORED <span style="font-family:var(--font-disp);font-size:1.8rem;color:var(--green)">${data.innings1_runs}</span> RUNS<br/>
          <span style="color:var(--amber)">${chaser.toUpperCase()}</span>
          NEEDS <span style="font-family:var(--font-disp);font-size:1.8rem;color:var(--amber)">${data.target}</span> TO WIN`;
        showScreen('screen-break');
      }, 1200);
    }
  } else {
    state.waitingNext = true;
    setTimeout(() => {
      state.waitingNext = false;
      document.getElementById('reveal-num-left').classList.remove('out-color');
      document.getElementById('reveal-num-right').classList.remove('out-color');
      banner.style.display = 'none';
      buildNumberGrid('game-number-grid', handleBall);
      if (state.target) {
        const needed = state.target - state.score;
        const el = document.getElementById('game-status');
        el.textContent = `SCORE: ${state.score} · NEED ${needed} MORE`;
        el.className = `status-line${needed <= 10 ? ' highlight' : ''}`;
      }
    }, 900);
  }
}

// ── PvP Mode game ─────────────────────────────────────────────────────────

function startPvPInnings(num) {
  state.innings      = num;
  state.pvpScore     = 0;
  state.pvpBallCount = 0;
  state.pvpPhase     = 'p1';
  state.pvpP1Num     = 0;
  state.pvpP2Num     = 0;

  const batter = num === 1 ? state.firstBatter
    : (state.firstBatter === state.playerName ? state.player2Name : state.playerName);
  const bowler = batter === state.playerName ? state.player2Name : state.playerName;

  document.getElementById('pvp-innings-label').textContent = `INNINGS ${num}`;
  document.getElementById('pvp-ball-log').innerHTML = '';
  document.getElementById('pvp-reveal-box').style.display = 'none';
  document.getElementById('pvp-result-banner').style.display = 'none';

  updatePvPScoreboard();
  setPvPTurn('p1', batter, bowler);
  buildNumberGrid('pvp-number-grid', handlePvPInput);
  showScreen('screen-pvp');
}

function updatePvPScoreboard() {
  const sb     = document.getElementById('pvp-scoreboard');
  const num    = state.innings;
  const batter = num === 1 ? state.firstBatter
    : (state.firstBatter === state.playerName ? state.player2Name : state.playerName);
  const needed = state.target ? state.target - state.pvpScore : null;

  if (num === 1) {
    sb.innerHTML = `
      <div class="score-box active-batter">
        <div class="score-name" style="color:var(--green)">${batter.toUpperCase()}</div>
        <div class="score-runs">${state.pvpScore}</div>
        <div class="score-label">BATTING</div>
      </div>
      <div class="score-box">
        <div class="score-name">—</div>
        <div class="score-runs">—</div>
        <div class="score-label">AWAITING</div>
      </div>`;
  } else {
    sb.innerHTML = `
      <div class="score-box">
        <div class="score-name">${state.firstBatter.toUpperCase()}</div>
        <div class="score-runs">${state.innings1Runs}</div>
        <div class="score-label">SET ${state.target}</div>
      </div>
      <div class="score-box active-batter">
        <div class="score-name" style="color:var(--blue)">${batter.toUpperCase()}</div>
        <div class="score-runs">${state.pvpScore}</div>
        <div class="score-label">CHASING${needed ? ' · NEEDS ' + needed : ''}</div>
      </div>`;
  }
}

function setPvPTurn(phase, batter, bowler) {
  const nameEl = document.getElementById('pvp-turn-name');
  const roleEl = document.getElementById('pvp-turn-role');
  if (phase === 'p1') {
    nameEl.textContent = batter.toUpperCase();
    nameEl.className   = `pvp-turn-name ${batter === state.playerName ? 'p1' : 'p2'}`;
    roleEl.textContent = 'BATTER — PICK YOUR NUMBER (keep hidden)';
  } else {
    nameEl.textContent = bowler.toUpperCase();
    nameEl.className   = `pvp-turn-name ${bowler === state.playerName ? 'p1' : 'p2'}`;
    roleEl.textContent = 'BOWLER — PICK YOUR NUMBER (keep hidden)';
  }
}

function handlePvPInput(num, btn) {
  disableGrid('pvp-number-grid');
  btn.classList.add(state.pvpPhase === 'p1' ? 'selected' : 'selected-p2');

  const batter = state.innings === 1 ? state.firstBatter
    : (state.firstBatter === state.playerName ? state.player2Name : state.playerName);
  const bowler = batter === state.playerName ? state.player2Name : state.playerName;

  if (state.pvpPhase === 'p1') {
    state.pvpP1Num = num;
    state.pvpPhase = 'p2';
    setTimeout(() => {
      setPvPTurn('p2', batter, bowler);
      buildNumberGrid('pvp-number-grid', handlePvPInput);
    }, 400);
  } else {
    state.pvpP2Num = num;
    resolvePvPBall(batter, bowler);
  }
}

async function resolvePvPBall(batter, bowler) {
  const batterNum = state.pvpP1Num;
  const bowlerNum = state.pvpP2Num;
  const out       = batterNum === bowlerNum;
  const runs      = out ? 0 : batterNum;

  state.pvpBallCount++;
  if (!out) state.pvpScore += runs;

  const revealBox = document.getElementById('pvp-reveal-box');
  revealBox.style.display = 'flex';
  document.getElementById('pvp-reveal-label-left').textContent  = batter.toUpperCase() + ' (BAT)';
  document.getElementById('pvp-reveal-label-right').textContent = bowler.toUpperCase() + ' (BOWL)';
  document.getElementById('pvp-reveal-num-left').textContent    = batterNum;
  document.getElementById('pvp-reveal-num-right').textContent   = bowlerNum;

  const banner = document.getElementById('pvp-result-banner');
  if (out) {
    banner.className   = 'result-banner out-banner';
    banner.textContent = `💥 OUT — BOTH CHOSE ${batterNum}`;
    banner.style.display = 'block';
    document.getElementById('pvp-reveal-num-left').classList.add('out-color');
    document.getElementById('pvp-reveal-num-right').classList.add('out-color');
  } else {
    banner.className   = 'result-banner safe-banner';
    banner.textContent = `+${runs} RUNS — TOTAL: ${state.pvpScore}`;
    banner.style.display = 'block';
  }

  addBallChip('pvp-ball-log', runs, out);
  updatePvPScoreboard();

  const won = state.target && state.pvpScore >= state.target;

  if (out || won) {
    setTimeout(() => {
      if (state.innings === 1) {
        state.innings1Runs = state.pvpScore;
        state.target       = state.pvpScore + 1;
        const chaser = batter === state.playerName ? state.player2Name : state.playerName;
        document.getElementById('break-message').innerHTML = `
          <span style="color:var(--green)">${batter.toUpperCase()}</span>
          SCORED <span style="font-family:var(--font-disp);font-size:1.8rem;color:var(--green)">${state.pvpScore}</span> RUNS<br/>
          <span style="color:var(--blue)">${chaser.toUpperCase()}</span>
          NEEDS <span style="font-family:var(--font-disp);font-size:1.8rem;color:var(--amber)">${state.target}</span> TO WIN`;
        showScreen('screen-break');
      } else {
        const winner = won ? batter : bowler;
        showPvPMatchOver(winner, state.innings1Runs, state.pvpScore);
      }
    }, 1500);
  } else {
    setTimeout(() => {
      document.getElementById('pvp-reveal-num-left').classList.remove('out-color');
      document.getElementById('pvp-reveal-num-right').classList.remove('out-color');
      banner.style.display    = 'none';
      revealBox.style.display = 'none';
      state.pvpPhase = 'p1';
      state.pvpP1Num = 0;
      state.pvpP2Num = 0;
      setPvPTurn('p1', batter, bowler);
      buildNumberGrid('pvp-number-grid', handlePvPInput);
      updatePvPScoreboard();
    }, 1200);
  }
}

function showPvPMatchOver(winner, i1runs, i2runs) {
  const wd = document.getElementById('winner-display');
  const chaser = state.firstBatter === state.playerName ? state.player2Name : state.playerName;
  wd.innerHTML = `
    <div class="trophy">🏆</div>
    <h2>${winner.toUpperCase()} WINS</h2>
    <p>${state.firstBatter.toUpperCase()}: ${i1runs} RUNS &nbsp;·&nbsp; ${chaser.toUpperCase()}: ${i2runs} RUNS</p>`;
  document.getElementById('insights-card').style.display = 'none';
  showScreen('screen-over');
}

// ── Match over (AI mode) ──────────────────────────────────────────────────

function showMatchOver(data) {
  const youWon = data.winner === state.playerName;
  const wd = document.getElementById('winner-display');
  wd.innerHTML = `
    <div class="trophy">${youWon ? '🏆' : '🤖'}</div>
    <h2 style="color:${youWon ? 'var(--green)' : 'var(--amber)'}">${data.winner.toUpperCase()} WINS</h2>
    <p>${state.playerName.toUpperCase()}: ${state.firstBatter === state.playerName ? data.innings1_runs : data.innings2_runs} RUNS
       &nbsp;·&nbsp; AI: ${state.firstBatter !== state.playerName ? data.innings1_runs : data.innings2_runs} RUNS</p>`;
  document.getElementById('insights-card').style.display = 'block';
  if (data.insights) renderInsights(data.insights);
  showScreen('screen-over');
}

function renderInsights(ins) {
  if (ins.message) return;
  const freq  = ins.number_frequency || {};
  const total = Object.values(freq).reduce((a, b) => a + b, 0) || 1;

  document.getElementById('insights-grid').innerHTML = `
    <div class="insight-stat">
      <div class="insight-label">FAVOURITE NUMBER</div>
      <div class="insight-value">${ins.favourite_number ?? '—'}</div>
    </div>
    <div class="insight-stat">
      <div class="insight-label">LEAST USED</div>
      <div class="insight-value amber">${ins.least_used_number ?? '—'}</div>
    </div>
    <div class="insight-stat">
      <div class="insight-label">FIRST BALL</div>
      <div class="insight-value" style="font-size:1rem;padding-top:0.5rem;">${ins.first_ball_tendency ?? '—'}</div>
    </div>
    <div class="insight-stat">
      <div class="insight-label">PREDICTABILITY</div>
      <div class="insight-value" style="font-size:0.85rem;padding-top:0.3rem;">${ins.predictability ?? '—'}</div>
    </div>`;

  const bars = document.getElementById('dist-bars');
  bars.innerHTML = '';
  for (let n = 1; n <= 10; n++) {
    const count = freq[n] ?? 0;
    const pct   = (count / total * 100).toFixed(1);
    const row   = document.createElement('div');
    row.className = 'dist-bar-row';
    row.innerHTML = `
      <span class="dist-num">${n}</span>
      <div class="dist-bar-bg"><div class="dist-bar-fill" style="width:${pct}%"></div></div>
      <span class="dist-pct">${pct}%</span>`;
    bars.appendChild(row);
  }
}

// ── Navigation ────────────────────────────────────────────────────────────

function playAgain() {
  state.score    = 0;
  state.ballCount = 0;
  state.target   = null;
  state.pvpScore = 0;
  document.getElementById('insights-card').style.display = 'block';
  startToss();
}

function goLobby() {
  document.getElementById('insights-card').style.display = 'block';
  loadPlayers();
}

function switchMode() {
  state.mode = state.mode === 'ai' ? 'pvp' : 'ai';
  document.getElementById('player-name-input').value = state.playerName;
  document.getElementById('p2-input-wrap').style.display = 'none';
  document.getElementById('pred-warning').style.display = 'none';
  showScreen('screen-login');
}

document.addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    const active = document.querySelector('.screen.active');
    if (active && active.id === 'screen-login') {
      const p2wrap = document.getElementById('p2-input-wrap');
      if (p2wrap.style.display === 'block') loadPlayers();
    }
  }
});
