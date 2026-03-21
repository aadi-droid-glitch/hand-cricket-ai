# 🏏 Hand Cricket AI

> *A passion project at the intersection of a schoolyard game, human psychology, and machine learning.*

Hand Cricket is a hand-sign based batting game invented by high schoolers around 2019. Two players reveal numbers 1–10 simultaneously using hand signs — same number means the batter is out. Simple rules, endlessly complex human behaviour underneath.

This project builds an AI that **plays the game, watches you play, and learns how predictable you really are.**

---

## What This Is

On the surface: a web app where you play Hand Cricket against an AI using your browser.

Under the surface: a **behavioural pattern recognition engine** that tracks every number you throw, the context you threw it in, and uses that data to bowl against you more intelligently over time.

The core thesis of this project is simple —

> *"Given enough balls, every player becomes predictable — even the ones who think they aren't."*

Humans don't truly randomise. They have favourite numbers, pressure responses, streak behaviours, and ego-driven patterns. This app finds yours.

---

## How Hand Cricket Works

**The Toss** — One player calls odd or even. Both reveal a number. Sum decides the winner.

**Batting phase** — Batter and bowler reveal numbers simultaneously using hand signs. Same number = batter is OUT. Different number = batter scores those runs. Continues until out.

**Chasing phase** — Second player targets first player's score + 1. Same rules apply. Gets out before target = first player wins. Reaches target = chaser wins.

**Super over** — If scores are tied, 6 ball sudden death round.

**Hand signs used:**

| Number | Sign |
|--------|------|
| 1 | Index finger only (no thumb) |
| 2 | Index + middle (no thumb) |
| 3 | Index + middle + ring (no thumb) |
| 4 | All four fingers (no thumb) |
| 5 | Perpendicular clap — both hands |
| 6 | Thumbs up 👍 |
| 7 | Thumb + index |
| 8 | Thumb + index + middle |
| 9 | Thumb + index + middle + ring |
| 10 | Namaste / parallel clap 🙏 |

---

## Architecture

```mermaid
flowchart TD
    subgraph INPUT["📷 Input Layer"]
        A[Camera Feed] --> B[MediaPipe Hand Tracking]
        B --> C[Gesture Decoder\nsign → number 1–10]
        C --> D[Timing Sync\ndetect reveal moment]
    end

    subgraph GAME["🎮 Game Engine"]
        E[Toss\nodd / even logic]
        F[Game Loop\nbat · bowl · score · out]
        G[Score Tracker\nchase · win · super over]
        E --> F --> G
    end

    subgraph BRAIN["🧠 Pattern Brain"]
        H[Context Collector\nscore · pressure · streak · milestone]
        I[Pattern Analyser\nfrequency + Markov chain]
        J[AI Predictor\nweighted probability bowl]
        K[Insights Dashboard\nyour patterns reflected back]
        H --> I --> J
        I --> K
    end

    subgraph STORAGE["🗄️ Storage — SQLite"]
        L[(Ball Log\nevery number + context)]
        M[(Player Profile\ncross-session memory)]
        N[(Session Log\nwins · runs · milestones)]
    end

    D --> F
    G --> H
    H --> L
    J --> M
    K --> N
    M -->|recall on game start| I
```

---

## Game Modes

### Player vs AI
Play against the pattern brain. The AI learns your tendencies over time and bowls smarter every session.

### Player vs Player
Two players on the same device. Turn-based input — Player 1 enters number secretly, then Player 2, then both revealed simultaneously. Full match with toss, innings, chase and super over.

---

## What The AI Tracks

Every single ball is logged with full context:

- The number thrown
- Current score at that moment
- Match state — normal / last 3 balls / super over / last ball
- Score bracket — 0–50 / 50–100 / 100–150 / 150+
- Streak length of current number
- Whether batting first or chasing

From this, the pattern brain builds a **probability table per player** that updates in real time. The AI bowls the number it thinks you're most likely to throw.

---

## Insights The App Shows You

**Predictability Score** — A single number showing how well the AI has modelled you. Updates every ball. Lower is better. Try to fool it.

**Pressure Heatmap** — A grid of score brackets vs numbers showing exactly where your behaviour shifts under pressure.

**Number Distribution** — Bar chart of how often you throw each number. Your giveaway numbers highlighted.

**First Ball Tendency** — Your most common opening number across all sessions.

---

## Tech Stack — 100% Free & Open Source

| Layer | Technology |
|-------|-----------|
| Gesture recognition | MediaPipe (Google, open source) |
| Backend + game logic | Python + FastAPI |
| Pattern brain | NumPy + Markov chain logic |
| Database | SQLite (local, zero setup) |
| Web frontend | HTML + CSS + Vanilla JS |
| Hosting (later) | Railway / Render free tier |

---

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Run the web app
uvicorn web.app:app --reload

# Open browser
http://localhost:8000

# Or play in terminal
python main.py
```

---

## Build Roadmap

- [x] **Phase 1** — Game engine (pure Python, terminal playable)
- [x] **Phase 2** — Pattern brain + SQLite data layer
- [x] **Phase 3A** — Web UI with FastAPI backend
- [ ] **Phase 3B** — MediaPipe gesture recognition (in progress)
- [x] **Phase 4** — PvP mode, polish, documentation
- [ ] **Phase 5 (V2)** — Mobile app via Flutter
- [ ] **Phase 6 (V2)** — Custom hand signs per player
- [ ] **Phase 7 (V2)** — AI batting strategy

---

## Known Limitations

**Gesture recognition** is orientation-sensitive. MediaPipe's rule-based landmark detection works well in consistent lighting and angles but struggles when hand orientation changes. A trained custom model for these specific 10 hand signs is planned for a future version.

**Single device PvP** requires trust — players must not peek at each other's input. A networked multiplayer version is a future goal.

---

## Why This Exists

This game has history. It was born in high school corridors around 2019, spread fast, survived COVID, and came back. Thousands of balls have been bowled with zero data collected.

This project changes that. It's part game, part experiment, part mirror — built to answer one question:

**Do you actually play randomly, or do you just think you do?**

---

## Known Limitations
Gesture recognition via MediaPipe is orientation-sensitive.
A trained custom model for these specific hand signs is 
planned for a future version.

---

*Built with curiosity. Powered by probability. Inspired by boring physics lectures.*
