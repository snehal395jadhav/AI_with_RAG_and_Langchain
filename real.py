import streamlit as st
import time
import datetime
import threading
import requests
import re

from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

# ══════════════════════════════════════════════════════════════
#  API KEY — hardcoded
# ══════════════════════════════════════════════════════════════
OPENROUTER_API_KEY = ""

# ══════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════
for k, v in {"mode": "standard"}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════
#  TOOL
# ══════════════════════════════════════════════════════════════
class DuckDuckGoTool(BaseTool):
    name: str = "web_search"
    description: str = "Search the internet. Input: plain-text search query."

    def _run(self, query: str) -> str:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            if not results:
                return "No results found."
            return "\n---\n".join(
                f"Title: {r.get('title','')}\nURL: {r.get('href','')}\nSummary: {r.get('body','')}"
                for r in results
            )
        except Exception:
            try:
                resp = requests.get(
                    f"https://html.duckduckgo.com/html/?q={query}",
                    headers={"User-Agent": "Mozilla/5.0"}, timeout=10
                )
                return resp.text[:3000]
            except Exception as e2:
                return f"Search failed: {e2}"

# ══════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(page_title="GAMEIQ · AI Research", page_icon="🎮",
                   layout="wide", initial_sidebar_state="collapsed")

# ══════════════════════════════════════════════════════════════
#  CSS  — Ultra-premium dark gaming + holographic UI
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Orbitron:wght@300;400;600;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap');

:root {
  --pink:#ff2d78;   --pink-dim:rgba(255,45,120,.18);
  --cyan:#00f5ff;   --cyan-dim:rgba(0,245,255,.15);
  --yellow:#ffe000; --yellow-dim:rgba(255,224,0,.15);
  --green:#39ff14;  --green-dim:rgba(57,255,20,.15);
  --orange:#ff6b00; --purple:#c020ff; --purple-dim:rgba(192,32,255,.15);
  --bg:#02000a;     --bg2:#07001a;    --card:#0a0020;
  --glass:rgba(255,255,255,.03);
  --border:rgba(255,255,255,.06);
  --text:#e0d8ff;   --text-dim:rgba(224,216,255,.5);
}

*, *::before, *::after { box-sizing: border-box; margin:0; padding:0; }

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Rajdhani', sans-serif !important;
  cursor: default !important;
}

/* ── Animated mesh background ── */
[data-testid="stAppViewContainer"]::before {
  content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
  background:
    radial-gradient(ellipse 80% 40% at 20% 10%, rgba(192,32,255,.07) 0%, transparent 60%),
    radial-gradient(ellipse 60% 30% at 80% 80%, rgba(0,245,255,.06) 0%, transparent 60%),
    radial-gradient(ellipse 50% 50% at 50% 50%, rgba(255,45,120,.04) 0%, transparent 70%),
    radial-gradient(1px 1px at 8%  12%,rgba(255,255,255,.6) 0%,transparent 100%),
    radial-gradient(1px 1px at 22% 58%,rgba(0,245,255,.5)   0%,transparent 100%),
    radial-gradient(1px 1px at 38% 28%,rgba(255,45,120,.6)  0%,transparent 100%),
    radial-gradient(1px 1px at 54% 78%,rgba(255,255,255,.4) 0%,transparent 100%),
    radial-gradient(1px 1px at 68% 18%,rgba(57,255,20,.5)   0%,transparent 100%),
    radial-gradient(1px 1px at 83% 52%,rgba(255,224,0,.6)   0%,transparent 100%),
    radial-gradient(1px 1px at 13% 88%,rgba(255,107,0,.5)   0%,transparent 100%),
    radial-gradient(1px 1px at 90%  8%,rgba(0,245,255,.7)   0%,transparent 100%),
    radial-gradient(1px 1px at 31% 43%,rgba(255,255,255,.5) 0%,transparent 100%),
    radial-gradient(1px 1px at 62% 72%,rgba(57,255,20,.4)   0%,transparent 100%),
    radial-gradient(1px 1px at 76% 36%,rgba(255,224,0,.5)   0%,transparent 100%);
  animation: bgPulse 8s ease-in-out infinite alternate;
}
@keyframes bgPulse {
  from { opacity:.7; }
  to   { opacity:1; }
}

/* CRT scanlines — very subtle */
[data-testid="stAppViewContainer"]::after {
  content:''; position:fixed; inset:0; pointer-events:none; z-index:1;
  background: repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,.08) 3px,rgba(0,0,0,.08) 4px);
}

#MainMenu, footer, header { visibility:hidden !important; }
[data-testid="stToolbar"] { display:none !important; }
.block-container { padding:0 2rem 4rem !important; max-width:1180px !important; position:relative; z-index:2; }
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:var(--bg2); }
::-webkit-scrollbar-thumb { background:var(--purple); border-radius:2px; }

/* ════════════ TOPBAR ════════════ */
.topbar {
  display:flex; align-items:center; justify-content:space-between;
  padding:.85rem 2rem;
  background:rgba(7,0,26,.9);
  border-bottom:1px solid rgba(192,32,255,.2);
  margin-bottom:0;
  backdrop-filter:blur(20px);
  position:sticky; top:0; z-index:100;
}
.topbar-logo {
  font-family:'Press Start 2P',monospace;
  font-size:.85rem;
  letter-spacing:.12em;
}
.topbar-logo .tl-g {color:var(--cyan);}
.topbar-logo .tl-a {color:var(--pink);}
.topbar-logo .tl-m {color:var(--yellow);}
.topbar-logo .tl-e {color:var(--green);}
.topbar-logo .tl-i {color:var(--orange);}
.topbar-logo .tl-q {color:var(--purple);}
.topbar-pills { display:flex; gap:.6rem; align-items:center; }
.topbar-pill {
  font-family:'Share Tech Mono',monospace; font-size:.6rem;
  padding:.25rem .7rem; border-radius:20px; letter-spacing:.08em;
}
.pill-green  { background:var(--green-dim);  border:1px solid var(--green);  color:var(--green);  }
.pill-cyan   { background:var(--cyan-dim);   border:1px solid var(--cyan);   color:var(--cyan);   }
.pill-yellow { background:var(--yellow-dim); border:1px solid var(--yellow); color:var(--yellow); }
.topbar-time { font-family:'Share Tech Mono',monospace; font-size:.58rem; color:var(--text-dim); }

/* ════════════ HERO SECTION ════════════ */
.hero {
  text-align:center;
  padding:3rem 1rem 1.5rem;
  position:relative;
  overflow:hidden;
}
.hero::before {
  content:'';
  position:absolute; inset:0;
  background: radial-gradient(ellipse 70% 60% at 50% 50%, rgba(192,32,255,.08) 0%, transparent 70%);
  animation:heroPulse 4s ease-in-out infinite alternate;
}
@keyframes heroPulse {
  from { opacity:.5; transform:scale(.95); }
  to   { opacity:1;  transform:scale(1.05); }
}

/* Floating pixels */
.pixel-particles { position:absolute; top:0; left:0; right:0; bottom:0; pointer-events:none; overflow:hidden; }
.pixel { position:absolute; border-radius:1px; animation:floatPixel linear infinite; }
.pixel:nth-child(1)  { background:var(--pink);   width:5px; height:5px; left:5%;  animation-duration:7s;  animation-delay:0s; }
.pixel:nth-child(2)  { background:var(--cyan);   width:4px; height:4px; left:15%; animation-duration:9s;  animation-delay:1s; }
.pixel:nth-child(3)  { background:var(--yellow); width:6px; height:6px; left:25%; animation-duration:6s;  animation-delay:2s; }
.pixel:nth-child(4)  { background:var(--green);  width:4px; height:4px; left:40%; animation-duration:10s; animation-delay:.5s; }
.pixel:nth-child(5)  { background:var(--orange); width:5px; height:5px; left:60%; animation-duration:8s;  animation-delay:1.5s; }
.pixel:nth-child(6)  { background:var(--cyan);   width:3px; height:3px; left:75%; animation-duration:7s;  animation-delay:3s; }
.pixel:nth-child(7)  { background:var(--pink);   width:5px; height:5px; left:88%; animation-duration:9s;  animation-delay:.8s; }
.pixel:nth-child(8)  { background:var(--yellow); width:4px; height:4px; left:50%; animation-duration:6s;  animation-delay:2.5s; }
.pixel:nth-child(9)  { background:var(--green);  width:6px; height:6px; left:95%; animation-duration:8s;  animation-delay:1.2s; }
.pixel:nth-child(10) { background:var(--purple); width:5px; height:5px; left:32%; animation-duration:10s; animation-delay:4s; }
@keyframes floatPixel {
  0%   { bottom:-10px; opacity:0; transform:rotate(0deg) scale(.5); }
  10%  { opacity:1; }
  90%  { opacity:.8; }
  100% { bottom:110%; opacity:0; transform:rotate(720deg) scale(1.2); }
}

.hero-title {
  font-family:'Orbitron',sans-serif;
  font-weight:900;
  font-size:clamp(2.5rem, 6vw, 5.5rem);
  letter-spacing:.08em;
  line-height:1.1;
  position:relative;
  display:inline-block;
}
.ht-g { color:var(--cyan);   text-shadow:0 0 20px var(--cyan),  0 0 60px rgba(0,245,255,.4),  0 0 120px rgba(0,245,255,.2);   animation:letterPop 3s ease-in-out infinite alternate; animation-delay:0s; }
.ht-a { color:var(--pink);   text-shadow:0 0 20px var(--pink),  0 0 60px rgba(255,45,120,.4),  0 0 120px rgba(255,45,120,.2);   animation:letterPop 3s ease-in-out infinite alternate; animation-delay:.2s; }
.ht-m { color:var(--yellow); text-shadow:0 0 20px var(--yellow),0 0 60px rgba(255,224,0,.4),  0 0 120px rgba(255,224,0,.2);   animation:letterPop 3s ease-in-out infinite alternate; animation-delay:.4s; }
.ht-e { color:var(--green);  text-shadow:0 0 20px var(--green), 0 0 60px rgba(57,255,20,.4),  0 0 120px rgba(57,255,20,.2);   animation:letterPop 3s ease-in-out infinite alternate; animation-delay:.6s; }
.ht-i { color:var(--orange); text-shadow:0 0 20px var(--orange),0 0 60px rgba(255,107,0,.4),  0 0 120px rgba(255,107,0,.2);   animation:letterPop 3s ease-in-out infinite alternate; animation-delay:.8s; }
.ht-q { color:var(--purple); text-shadow:0 0 20px var(--purple),0 0 60px rgba(192,32,255,.4), 0 0 120px rgba(192,32,255,.2);  animation:letterPop 3s ease-in-out infinite alternate; animation-delay:1s; }
@keyframes letterPop { from{filter:brightness(1)} to{filter:brightness(1.4)} }

.hero-sub {
  font-family:'Share Tech Mono',monospace;
  font-size:.75rem; letter-spacing:.35em; color:var(--yellow);
  text-shadow:0 0 10px rgba(255,224,0,.5);
  margin-top:.8rem; text-transform:uppercase;
  animation:subBlink 2s step-end infinite;
}
@keyframes subBlink { 0%,100%{opacity:1} 49%{opacity:1} 50%,99%{opacity:.35} }

.hero-tagline {
  font-family:'Rajdhani',sans-serif;
  font-size:1rem; font-weight:300;
  color:var(--text-dim); letter-spacing:.12em;
  margin-top:.5rem; text-transform:uppercase;
}

/* ════════════ RAINBOW BAR ════════════ */
.rainbow-bar {
  height:2px;
  background:linear-gradient(90deg,var(--pink) 0%,var(--orange) 20%,var(--yellow) 40%,var(--green) 60%,var(--cyan) 80%,var(--purple) 100%);
  background-size:300% 100%;
  animation:rainbowSlide 4s linear infinite;
  margin:.8rem 0; border-radius:1px;
  box-shadow:0 0 8px rgba(0,245,255,.3), 0 0 20px rgba(192,32,255,.2);
}
@keyframes rainbowSlide { from{background-position:0%} to{background-position:300%} }

/* ════════════ STATS GRID ════════════ */
.stats-grid {
  display:grid; grid-template-columns:repeat(5,1fr); gap:.8rem;
  margin:1.2rem 0;
}
.stat-block {
  background:var(--glass);
  border:1px solid var(--border);
  border-radius:10px;
  padding:.9rem .7rem;
  text-align:center;
  position:relative;
  overflow:hidden;
  transition:border-color .3s;
}
.stat-block::before {
  content:''; position:absolute; top:0; left:0; right:0; height:1px;
  background:linear-gradient(90deg,transparent,var(--accent,var(--cyan)),transparent);
  animation:topScan 3s linear infinite;
}
@keyframes topScan { from{background-position:-100%} to{background-position:200%} }
.stat-block:hover { border-color:var(--accent,var(--cyan)); }
.stat-label { font-family:'Press Start 2P',monospace; font-size:.38rem; letter-spacing:.1em; margin-bottom:.4rem; }
.stat-bar-wrap { height:6px; background:rgba(255,255,255,.07); border-radius:3px; overflow:hidden; margin-bottom:.4rem; }
.stat-bar { height:100%; border-radius:3px; animation:barFill 2.5s ease-out both; }
@keyframes barFill { from{width:0!important} }
.stat-val { font-family:'Orbitron',sans-serif; font-size:.6rem; font-weight:700; }

/* ════════════ SECTION HEADERS ════════════ */
.section-header {
  display:flex; align-items:center; gap:.8rem;
  padding:.6rem 0; margin:1.4rem 0 .8rem;
  border-bottom:1px solid var(--border);
}
.section-num {
  font-family:'Press Start 2P',monospace; font-size:.5rem;
  color:var(--purple); opacity:.6; min-width:2rem;
}
.section-title {
  font-family:'Orbitron',monospace; font-size:.75rem;
  font-weight:700; letter-spacing:.2em; text-transform:uppercase;
}
.section-line { flex:1; height:1px; background:linear-gradient(90deg,var(--border),transparent); }

/* ════════════ MODE CARDS ════════════ */
.mode-grid-wrap { display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin:.5rem 0 1.5rem; }
.mode-card {
  background:rgba(10,0,28,.8);
  border:1px solid var(--border);
  border-radius:12px;
  padding:1.4rem 1rem 1.1rem;
  text-align:center;
  position:relative;
  overflow:hidden;
  transition:all .3s cubic-bezier(.2,1,.4,1);
  cursor:pointer;
}
.mode-card::after {
  content:''; position:absolute; inset:0; border-radius:12px;
  background:linear-gradient(135deg,rgba(255,255,255,.03) 0%,transparent 60%);
}
.mode-card:hover { transform:translateY(-4px); }
.mode-card.sel { transform:translateY(-6px); }

.mode-card.sel-standard { border-color:var(--cyan);   box-shadow:0 8px 30px rgba(0,245,255,.2),  inset 0 1px 0 rgba(0,245,255,.1); }
.mode-card.sel-debate   { border-color:var(--pink);   box-shadow:0 8px 30px rgba(255,45,120,.2), inset 0 1px 0 rgba(255,45,120,.1); }
.mode-card.sel-slides   { border-color:var(--yellow); box-shadow:0 8px 30px rgba(255,224,0,.2),  inset 0 1px 0 rgba(255,224,0,.1); }
.mode-card.sel-trends   { border-color:var(--green);  box-shadow:0 8px 30px rgba(57,255,20,.2),  inset 0 1px 0 rgba(57,255,20,.1); }

.mode-emoji { font-size:2rem; margin-bottom:.6rem; display:block; animation:emojiFloat 3s ease-in-out infinite; }
@keyframes emojiFloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
.mode-name {
  font-family:'Orbitron',sans-serif; font-weight:700;
  font-size:.72rem; letter-spacing:.1em; margin-bottom:.3rem;
}
.mode-sub {
  font-family:'Share Tech Mono',monospace; font-size:.55rem;
  color:var(--text-dim); margin-bottom:.45rem; letter-spacing:.06em;
}
.mode-desc { font-family:'Rajdhani',sans-serif; font-size:.8rem; color:rgba(255,255,255,.4); line-height:1.5; margin-bottom:.55rem; }
.mode-tag {
  font-family:'Press Start 2P',monospace; font-size:.3rem;
  padding:.18rem .45rem; border-radius:20px; display:inline-block;
  letter-spacing:.1em;
}

/* ════════════ INPUT PANEL ════════════ */
.quest-panel {
  background:rgba(8,0,22,.85);
  border:1px solid rgba(0,245,255,.2);
  border-radius:14px;
  padding:1.8rem 2rem;
  margin-bottom:1.5rem;
  position:relative;
  backdrop-filter:blur(10px);
  transition:border-color .3s;
}
.quest-panel:focus-within { border-color:rgba(0,245,255,.5); box-shadow:0 0 30px rgba(0,245,255,.08); }
.quest-panel::before {
  content:'MISSION BRIEFING';
  position:absolute; top:-11px; left:20px;
  background:var(--bg); padding:0 10px;
  font-family:'Share Tech Mono',monospace; font-size:.55rem;
  color:var(--cyan); letter-spacing:.2em;
}

/* Inputs */
[data-testid="stTextInput"] > div > div {
  background:transparent !important;
}
[data-testid="stTextInput"] input {
  background: rgba(0,0,15,.6) !important;
  border:1px solid rgba(0,245,255,.2) !important;
  border-radius:8px !important;
  color:#fff !important;
  font-family:'Rajdhani',sans-serif !important;
  font-size:1.05rem !important;
  font-weight:500 !important;
  letter-spacing:.04em !important;
  padding:.9rem 1.2rem !important;
  caret-color:var(--cyan) !important;
  transition:all .25s !important;
}
[data-testid="stTextInput"] input:focus {
  border-color:rgba(0,245,255,.6) !important;
  background:rgba(0,5,30,.8) !important;
  box-shadow:0 0 0 3px rgba(0,245,255,.08) !important;
  outline:none !important;
}
[data-testid="stTextInput"] input::placeholder { color:rgba(255,255,255,.2) !important; }
[data-testid="stTextInput"] label {
  font-family:'Share Tech Mono',monospace !important;
  font-size:.6rem !important;
  letter-spacing:.2em !important;
  color:rgba(0,245,255,.6) !important;
  text-transform:uppercase !important;
  margin-bottom:.3rem !important;
}

/* ════════════ LAUNCH BUTTON ════════════ */
[data-testid="stButton"] button {
  background:linear-gradient(135deg, rgba(255,45,120,.9) 0%, rgba(192,32,255,.9) 50%, rgba(255,107,0,.9) 100%) !important;
  border:none !important;
  border-radius:10px !important;
  color:#fff !important;
  font-family:'Orbitron',sans-serif !important;
  font-size:.75rem !important;
  font-weight:700 !important;
  letter-spacing:.15em !important;
  padding:.95rem 2rem !important;
  cursor:pointer !important;
  width:100% !important;
  transition:all .2s !important;
  text-transform:uppercase !important;
  position:relative !important;
  overflow:hidden !important;
  box-shadow:0 4px 20px rgba(255,45,120,.35), 0 0 40px rgba(192,32,255,.2) !important;
  animation:launchPulse 2.5s ease-in-out infinite !important;
}
@keyframes launchPulse {
  0%,100% { box-shadow:0 4px 20px rgba(255,45,120,.35),0 0 40px rgba(192,32,255,.2); }
  50%     { box-shadow:0 4px 35px rgba(255,45,120,.65),0 0 60px rgba(192,32,255,.4); }
}
[data-testid="stButton"] button:hover { transform:translateY(-3px) scale(1.01) !important; filter:brightness(1.15) !important; }
[data-testid="stButton"] button:active { transform:scale(.98) !important; }

/* ════════════ MODE INFO BAR ════════════ */
.mode-info-bar {
  display:flex; align-items:center; gap:.6rem;
  padding:.5rem .8rem; border-radius:6px;
  background:rgba(0,245,255,.05);
  border:1px solid rgba(0,245,255,.1);
  font-family:'Share Tech Mono',monospace; font-size:.55rem;
  color:rgba(0,245,255,.6); letter-spacing:.1em;
  margin-top:.8rem;
}
.mib-dot { width:6px; height:6px; border-radius:50%; background:var(--green); box-shadow:0 0 6px var(--green); animation:dotBlink 1s step-end infinite; }
@keyframes dotBlink { 0%,100%{opacity:1} 50%{opacity:.2} }

/* ════════════ AGENT CARDS ════════════ */
.agent-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1.2rem; margin:1.2rem 0; }
.agent-card {
  background:rgba(10,0,28,.8);
  border:1px solid var(--border);
  border-radius:12px;
  padding:1.6rem 1rem;
  text-align:center;
  position:relative;
  overflow:hidden;
  transition:all .4s cubic-bezier(.2,1,.4,1);
}
.agent-card::before {
  content:''; position:absolute; top:-50%; left:-50%; width:200%; height:200%;
  background:conic-gradient(from 0deg,transparent,rgba(0,245,255,.05) 60deg,transparent 120deg);
  animation:cardSpin 8s linear infinite; opacity:0; transition:opacity .4s;
}
.agent-card.active::before { opacity:1; }
@keyframes cardSpin { to{transform:rotate(360deg)} }

.agent-card.idle   { border-color:rgba(255,255,255,.07); }
.agent-card.active {
  border-color:var(--cyan);
  box-shadow:0 0 25px rgba(0,245,255,.25), 0 0 60px rgba(0,245,255,.08);
  transform:translateY(-6px);
  background:rgba(0,15,40,.9);
}
.agent-card.done {
  border-color:rgba(57,255,20,.4);
  box-shadow:0 0 15px rgba(57,255,20,.2);
}

.agent-icon { font-size:2.4rem; display:block; margin-bottom:.6rem; }
.agent-card.active .agent-icon { animation:iconFloat .9s ease-in-out infinite; }
.agent-card.idle   .agent-icon { animation:iconFloat 3s ease-in-out infinite; }
.agent-card.done   .agent-icon { animation:iconFloat 5s ease-in-out infinite; }
@keyframes iconFloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }

.agent-name {
  font-family:'Orbitron',sans-serif; font-weight:700;
  font-size:.8rem; letter-spacing:.12em; margin-bottom:.2rem;
}
.agent-card.idle   .agent-name { color:rgba(255,255,255,.3); }
.agent-card.active .agent-name { color:var(--cyan); text-shadow:0 0 10px rgba(0,245,255,.5); }
.agent-card.done   .agent-name { color:var(--green); text-shadow:0 0 8px rgba(57,255,20,.4); }

.agent-role { font-family:'Rajdhani',sans-serif; font-size:.78rem; color:rgba(255,255,255,.28); margin-bottom:.6rem; letter-spacing:.06em; }

.agent-status {
  font-family:'Share Tech Mono',monospace; font-size:.5rem;
  letter-spacing:.08em; padding:.22rem .6rem; border-radius:20px;
  display:inline-block;
}
.agent-card.idle   .agent-status { background:rgba(255,255,255,.04); color:rgba(255,255,255,.22); border:1px solid rgba(255,255,255,.06); }
.agent-card.active .agent-status { background:rgba(0,245,255,.1); color:var(--cyan); border:1px solid rgba(0,245,255,.3); animation:statusPulse .9s step-end infinite; }
.agent-card.done   .agent-status { background:rgba(57,255,20,.1); color:var(--green); border:1px solid rgba(57,255,20,.3); }
@keyframes statusPulse { 0%,100%{opacity:1} 50%{opacity:.3} }

.agent-progress { height:2px; background:rgba(255,255,255,.05); border-radius:1px; margin-top:1rem; overflow:hidden; }
.agent-progress-fill { height:100%; border-radius:1px; transition:width .8s ease; }
.agent-card.active .agent-progress-fill { background:linear-gradient(90deg,var(--cyan),var(--purple)); background-size:200%; animation:progFlow 1.2s linear infinite; }
.agent-card.done   .agent-progress-fill { background:var(--green); box-shadow:0 0 6px var(--green); }
@keyframes progFlow { from{background-position:0%} to{background-position:200%} }

/* ════════════ TERMINAL ════════════ */
.terminal-box {
  background:rgba(0,3,8,.95);
  border:1px solid rgba(57,255,20,.3);
  border-radius:10px;
  padding:1.2rem 1.6rem;
  margin:1rem 0;
  position:relative;
  overflow:hidden;
  box-shadow:0 0 20px rgba(57,255,20,.1), inset 0 0 20px rgba(0,0,0,.5);
}
.terminal-box::before {
  content:'SYSTEM TERMINAL';
  position:absolute; top:-10px; left:16px;
  background:var(--bg); padding:0 8px;
  font-family:'Share Tech Mono',monospace; font-size:.48rem;
  color:rgba(57,255,20,.6); letter-spacing:.15em;
}
.terminal-phase {
  font-family:'Share Tech Mono',monospace; font-size:.6rem;
  color:var(--yellow); letter-spacing:.1em; margin-bottom:.5rem;
}
.terminal-msg {
  font-family:'Share Tech Mono',monospace; font-size:.65rem;
  color:var(--green); letter-spacing:.06em; line-height:1.9;
}
.terminal-meta {
  font-family:'Share Tech Mono',monospace; font-size:.5rem;
  color:rgba(57,255,20,.4); letter-spacing:.08em; margin-top:.5rem; border-top:1px solid rgba(57,255,20,.1); padding-top:.4rem;
}
.terminal-sub {
  font-family:'Share Tech Mono',monospace; font-size:.52rem;
  color:rgba(0,245,255,.45); letter-spacing:.08em; margin-top:.25rem;
}
.cursor { display:inline-block; width:7px; height:13px; background:var(--green); animation:blink .7s step-end infinite; vertical-align:middle; margin-left:2px; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* ════════════ LIVE OUTPUT ════════════ */
.live-out {
  background:rgba(0,5,20,.97);
  border:1px solid rgba(0,245,255,.2);
  border-radius:10px;
  padding:1.4rem 1.8rem;
  margin:.8rem 0;
  position:relative;
  max-height:280px; overflow-y:auto;
  box-shadow:0 0 15px rgba(0,245,255,.08);
}
.live-out::before {
  content:'LIVE OUTPUT';
  position:absolute; top:-10px; left:16px;
  background:var(--bg); padding:0 8px;
  font-family:'Share Tech Mono',monospace; font-size:.48rem;
  color:rgba(0,245,255,.5); letter-spacing:.15em;
}
.live-out-text { font-family:'Rajdhani',sans-serif; font-size:.9rem; color:rgba(160,220,255,.8); line-height:1.9; white-space:pre-wrap; word-break:break-word; }
.live-cursor { display:inline-block; width:9px; height:15px; background:var(--cyan); animation:blink .6s step-end infinite; vertical-align:middle; margin-left:3px; }

/* ════════════ RESULT PANELS ════════════ */
.result-panel {
  border-radius:14px; padding:2.5rem; margin-top:1.5rem;
  position:relative; animation:panelReveal .7s cubic-bezier(.2,1,.4,1) both;
}
@keyframes panelReveal { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:none} }

.result-panel.standard { background:rgba(5,0,20,.97); border:1px solid rgba(255,45,120,.3); box-shadow:0 0 40px rgba(255,45,120,.1); }
.result-panel.debate   { background:rgba(5,0,20,.97); border:1px solid rgba(255,45,120,.3); box-shadow:0 0 40px rgba(255,45,120,.1); }
.result-panel.slides   { background:rgba(0,5,20,.97); border:1px solid rgba(255,224,0,.25); box-shadow:0 0 40px rgba(255,224,0,.08); }
.result-panel.trends   { background:rgba(0,5,8,.97);  border:1px solid rgba(57,255,20,.25); box-shadow:0 0 40px rgba(57,255,20,.08); }

.result-panel-label {
  position:absolute; top:-12px; left:20px;
  background:var(--bg); padding:0 12px;
  font-family:'Share Tech Mono',monospace; font-size:.48rem;
  letter-spacing:.15em; text-transform:uppercase;
}
.result-panel.standard .result-panel-label,
.result-panel.debate   .result-panel-label { color:var(--pink); }
.result-panel.slides   .result-panel-label { color:var(--yellow); }
.result-panel.trends   .result-panel-label { color:var(--green); }

.result-content { font-family:'Rajdhani',sans-serif; font-size:1rem; line-height:2; color:rgba(220,210,255,.9); }
.result-content h1 { font-family:'Orbitron',sans-serif; color:var(--pink);   font-size:1.3rem; margin:1.2rem 0 .5rem; letter-spacing:.08em; }
.result-content h2 { font-family:'Orbitron',sans-serif; color:var(--cyan);   font-size:1.1rem; margin:1rem 0 .4rem; letter-spacing:.07em; }
.result-content h3 { font-family:'Orbitron',sans-serif; color:var(--yellow); font-size:.95rem; margin:.8rem 0 .3rem; letter-spacing:.06em; }
.result-content .bullet { color:rgba(176,224,255,.8); padding-left:1.2rem; margin:.2rem 0; }
.result-content .bullet::before { content:'▸ '; color:var(--cyan); }

/* Meta footer */
.result-meta {
  display:flex; flex-wrap:wrap; gap:.6rem; justify-content:space-between;
  border-top:1px solid rgba(255,255,255,.06);
  margin-top:1.8rem; padding-top:1rem;
}
.meta-chip {
  font-family:'Share Tech Mono',monospace; font-size:.48rem;
  color:rgba(255,255,255,.25); letter-spacing:.1em;
  padding:.2rem .55rem; background:rgba(255,255,255,.03);
  border:1px solid rgba(255,255,255,.06); border-radius:4px;
}
.meta-chip span { color:var(--yellow); }

/* ════════════ DOWNLOAD BUTTON ════════════ */
[data-testid="stDownloadButton"] button {
  background:rgba(57,255,20,.06) !important;
  border:1px solid rgba(57,255,20,.4) !important;
  border-radius:10px !important;
  color:var(--green) !important;
  font-family:'Orbitron',sans-serif !important;
  font-size:.65rem !important;
  font-weight:600 !important;
  letter-spacing:.15em !important;
  padding:.9rem 1.5rem !important;
  margin-top:1.2rem !important;
  width:100% !important;
  transition:all .3s !important;
  animation:dlPulse 2.5s ease-in-out infinite !important;
}
@keyframes dlPulse { 0%,100%{box-shadow:0 0 12px rgba(57,255,20,.2)} 50%{box-shadow:0 0 25px rgba(57,255,20,.45)} }
[data-testid="stDownloadButton"] button:hover { background:rgba(57,255,20,.15) !important; transform:translateY(-2px) !important; }

/* ════════════ VICTORY ════════════ */
.victory-wrap {
  text-align:center; padding:1.5rem 0;
  animation:fadeUp .6s cubic-bezier(.2,1,.4,1) both;
}
.victory-text {
  font-family:'Orbitron',sans-serif; font-weight:900;
  font-size:clamp(.9rem,2.5vw,1.6rem);
  color:var(--yellow);
  text-shadow:0 0 20px var(--yellow), 0 0 50px rgba(255,224,0,.5), 0 0 100px rgba(255,224,0,.3);
  letter-spacing:.12em; text-transform:uppercase;
}

/* ════════════ ERROR ════════════ */
.err-box {
  background:rgba(255,45,120,.06);
  border:1px solid rgba(255,45,120,.4);
  border-radius:8px;
  padding:.9rem 1.4rem; margin:.6rem 0;
  font-family:'Share Tech Mono',monospace; font-size:.55rem;
  color:var(--pink); letter-spacing:.1em; line-height:2;
  animation:fadeUp .4s ease both;
}

@keyframes fadeUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:none} }
.fade-in { animation:fadeUp .5s ease both; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TOPBAR
# ══════════════════════════════════════════════════════════════
now = datetime.datetime.now()
st.markdown(f"""
<div class="topbar">
  <div class="topbar-logo">
    <span class="tl-g">G</span><span class="tl-a">A</span><span class="tl-m">M</span><span class="tl-e">E</span><span class="tl-i">I</span><span class="tl-q">Q</span>
  </div>
  <div class="topbar-pills">
    <span class="topbar-pill pill-green">● ONLINE</span>
    <span class="topbar-pill pill-cyan">GPT-3.5-TURBO</span>
    <span class="topbar-pill pill-yellow">3 AGENTS</span>
  </div>
  <div class="topbar-time">{now.strftime('%a %d %b %Y &nbsp; %H:%M:%S')}</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  HERO
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <div class="pixel-particles">
    <div class="pixel"></div><div class="pixel"></div><div class="pixel"></div>
    <div class="pixel"></div><div class="pixel"></div><div class="pixel"></div>
    <div class="pixel"></div><div class="pixel"></div><div class="pixel"></div>
    <div class="pixel"></div>
  </div>
  <div class="hero-title">
    <span class="ht-g">G</span><span class="ht-a">A</span><span class="ht-m">M</span><span class="ht-e">E</span><span class="ht-i">I</span><span class="ht-q">Q</span>
  </div>
  <div class="hero-sub">▶ AI Research Intelligence System ◀</div>
  <div class="hero-tagline">Multi-Agent · Web-Powered · Four Research Modes</div>
</div>
<div class="rainbow-bar"></div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  STATS GRID
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="stats-grid fade-in">
  <div class="stat-block" style="--accent:var(--cyan)">
    <div class="stat-label" style="color:var(--cyan)">INTELLIGENCE</div>
    <div class="stat-bar-wrap"><div class="stat-bar" style="width:95%;background:linear-gradient(90deg,var(--cyan),#0080ff)"></div></div>
    <div class="stat-val" style="color:var(--cyan)">95 / 100</div>
  </div>
  <div class="stat-block" style="--accent:var(--pink)">
    <div class="stat-label" style="color:var(--pink)">RESEARCH PWR</div>
    <div class="stat-bar-wrap"><div class="stat-bar" style="width:88%;background:linear-gradient(90deg,var(--pink),var(--orange))"></div></div>
    <div class="stat-val" style="color:var(--pink)">88 / 100</div>
  </div>
  <div class="stat-block" style="--accent:var(--yellow)">
    <div class="stat-label" style="color:var(--yellow)">SPEED</div>
    <div class="stat-bar-wrap"><div class="stat-bar" style="width:78%;background:linear-gradient(90deg,var(--yellow),var(--orange))"></div></div>
    <div class="stat-val" style="color:var(--yellow)">78 / 100</div>
  </div>
  <div class="stat-block" style="--accent:var(--green)">
    <div class="stat-label" style="color:var(--green)">ACCURACY</div>
    <div class="stat-bar-wrap"><div class="stat-bar" style="width:92%;background:linear-gradient(90deg,var(--green),var(--cyan))"></div></div>
    <div class="stat-val" style="color:var(--green)">92 / 100</div>
  </div>
  <div class="stat-block" style="--accent:var(--purple)">
    <div class="stat-label" style="color:var(--purple)">AGENTS</div>
    <div class="stat-bar-wrap"><div class="stat-bar" style="width:100%;background:linear-gradient(90deg,var(--purple),var(--pink))"></div></div>
    <div class="stat-val" style="color:var(--purple)">3 / 3</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  MODE SELECTOR
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-header">
  <span class="section-num">01</span>
  <span class="section-title" style="color:var(--yellow)">Select Activity Mode</span>
  <span class="section-line"></span>
</div>
""", unsafe_allow_html=True)

MODES = [
    ("standard", "📋", "STANDARD",   "Research Report",  "Full multi-agent research → structured report + PDF",   "var(--cyan)",   "CLASSIC", "cyan"),
    ("debate",   "🧠", "AI DEBATE",  "Argue All Sides",  "3 agents argue PRO / CON / NEUTRAL with final verdict", "var(--pink)",   "HOT",     "pink"),
    ("slides",   "📊", "SLIDE DECK", "Auto PPT Outline", "10-slide presentation outline with speaker notes",      "var(--yellow)", "NEW",     "yellow"),
    ("trends",   "🌍", "TREND SCAN", "Live Web Analysis","Trending angles · sentiment · emerging sub-topics",     "var(--green)",  "LIVE",    "green"),
]

mode_cols = st.columns(4)
for col, (key, icon, name, sub, desc, color, badge, cname) in zip(mode_cols, MODES):
    with col:
        sel = "sel sel-" + key if st.session_state.mode == key else ""
        st.markdown(f"""
        <div class="mode-card {sel}">
          <span class="mode-emoji">{icon}</span>
          <div class="mode-name" style="color:{color}">{name}</div>
          <div class="mode-sub">{sub}</div>
          <div class="mode-desc">{desc}</div>
          <div class="mode-tag" style="background:var(--{cname}-dim,rgba(255,255,255,.05));color:{color};border:1px solid {color}">{badge}</div>
        </div>""", unsafe_allow_html=True)
        if st.button(f"▶ {name}", key=f"sel_{key}"):
            st.session_state.mode = key
            st.rerun()

# ══════════════════════════════════════════════════════════════
#  QUEST INPUT
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-header">
  <span class="section-num">02</span>
  <span class="section-title" style="color:var(--cyan)">Mission Briefing</span>
  <span class="section-line"></span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="quest-panel">', unsafe_allow_html=True)

topic = st.text_input(
    "Research Quest Topic",
    placeholder="e.g.  History of Video Games  ·  AI in eSports  ·  Future of Game Development",
)

mode_display = {"standard":"STANDARD REPORT","debate":"AI DEBATE","slides":"SLIDE DECK","trends":"TREND SCAN"}
col_info, col_btn = st.columns([3,1])
with col_info:
    st.markdown(f"""
    <div class="mode-info-bar">
      <div class="mib-dot"></div>
      MODE: {mode_display[st.session_state.mode]} &nbsp;·&nbsp;
      MODEL: GPT-3.5-TURBO &nbsp;·&nbsp;
      PROVIDER: OPENROUTER &nbsp;·&nbsp;
      AGENTS: 3
    </div>""", unsafe_allow_html=True)
with col_btn:
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    run = st.button("🚀 LAUNCH AGENTS")

st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  AGENT CARDS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-header" style="margin-top:1rem">
  <span class="section-num">03</span>
  <span class="section-title" style="color:var(--purple)">Agent Status</span>
  <span class="section-line"></span>
</div>
""", unsafe_allow_html=True)

agent_ph = st.empty()

MODE_AGENTS = {
    "standard": [("🔍","SCOUT","Web Recon Agent","Gathering intel..."),("✍️","SCRIBE","Report Writer","Crafting report..."),("⚔️","JUDGE","QA Reviewer","Final polish...")],
    "debate":   [("🔴","PRO","Argues For","Building case..."),("🔵","CON","Argues Against","Countering..."),("⚖️","NEUTRAL","Moderator","Summarising...")],
    "slides":   [("🔍","SCOUT","Content Researcher","Finding facts..."),("🖼️","DESIGNER","Slide Architect","Building deck..."),("✅","POLISH","Slide Reviewer","Polishing...")],
    "trends":   [("📡","CRAWLER","Trend Scout","Scanning web..."),("📈","ANALYST","Data Analyst","Analysing..."),("📣","REPORTER","Trend Reporter","Writing report...")],
}

def show_agents(active=None, done_list=None):
    done_list = done_list or []
    agents = MODE_AGENTS[st.session_state.mode]
    cards = []
    for i, (icon, name, role, doing) in enumerate(agents):
        if i in done_list:
            css, status, hp = "done",   "✓ COMPLETE", "100%"
        elif active == i:
            css, status, hp = "active", doing,         "65%"
        else:
            css, status, hp = "idle",   "STANDBY",     "0%"
        cards.append(f"""
        <div class="agent-card {css}">
          <span class="agent-icon">{icon}</span>
          <div class="agent-name">{name}</div>
          <div class="agent-role">{role}</div>
          <div class="agent-status">{status}</div>
          <div class="agent-progress"><div class="agent-progress-fill" style="width:{hp}"></div></div>
        </div>""")
    agent_ph.markdown(f'<div class="agent-grid">{"".join(cards)}</div>', unsafe_allow_html=True)

show_agents()

# ══════════════════════════════════════════════════════════════
#  PDF GENERATOR
# ══════════════════════════════════════════════════════════════
def generate_pdf(text: str, topic: str, mode: str) -> bytes:
    from io import BytesIO
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=55, bottomMargin=55)
    ML = {"standard":"Research Report","debate":"AI Debate Summary","slides":"Slide Deck Outline","trends":"Trend Analysis"}
    ts = ParagraphStyle("T", fontName="Helvetica-Bold", fontSize=22, textColor=colors.HexColor("#cc0055"), alignment=TA_CENTER, spaceAfter=6)
    ss = ParagraphStyle("S", fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#0066aa"), alignment=TA_CENTER, spaceAfter=4)
    hs = ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=13, textColor=colors.HexColor("#7700cc"), spaceBefore=14, spaceAfter=6)
    bs = ParagraphStyle("B", fontName="Helvetica", fontSize=11, textColor=colors.HexColor("#1a1030"), leading=19, spaceAfter=4, alignment=TA_JUSTIFY)
    bls= ParagraphStyle("BL",fontName="Helvetica", fontSize=11, textColor=colors.HexColor("#220044"), leading=18, spaceAfter=3, leftIndent=16)

    story = [
        Paragraph(f"GAMEIQ — {ML.get(mode,'Report').upper()}", ts),
        Paragraph(f"Topic: {topic}", ss),
        Paragraph(f"Mode: {ML.get(mode)} · Model: GPT-3.5-Turbo via OpenRouter", ss),
        Paragraph(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC')}", ss),
        Spacer(1,8), HRFlowable(width="100%",thickness=2,color=colors.HexColor("#ff2d78")), Spacer(1,14),
    ]
    clean = re.sub(r'CrewOutput\(.*?raw=["\']','', str(text), flags=re.DOTALL)
    clean = re.sub(r'["\'],\s*agent.*$','', clean, flags=re.DOTALL).strip() or str(text)
    for line in clean.split("\n"):
        s = line.strip()
        if not s: story.append(Spacer(1,6))
        elif s.startswith("### "): story.append(Paragraph(s[4:], hs))
        elif s.startswith("## "):  story.append(Paragraph(s[3:], hs))
        elif s.startswith("# "):   story.append(Paragraph(s[2:], hs))
        elif s.startswith("**") and s.endswith("**"): story.append(Paragraph(s.replace("**",""), hs))
        elif s.startswith("- ") or s.startswith("* "): story.append(Paragraph("• "+s[2:], bls))
        else: story.append(Paragraph(re.sub(r'\*\*(.*?)\*\*',r'\1',s), bs))
    story += [Spacer(1,20), HRFlowable(width="100%",thickness=1,color=colors.HexColor("#cc0055")), Spacer(1,6),
              Paragraph("GAMEIQ AI Research System · CrewAI + GPT-3.5-Turbo via OpenRouter", ss)]
    doc.build(story)
    return buf.getvalue()

# ══════════════════════════════════════════════════════════════
#  HTML RENDERER
# ══════════════════════════════════════════════════════════════
def render_html(raw: str) -> str:
    parts = []
    for line in str(raw).split("\n"):
        s = line.strip()
        if not s: parts.append("<br>")
        elif s.startswith("### "): parts.append(f'<h3 class="result-content" style="color:var(--yellow)">{s[4:]}</h3>')
        elif s.startswith("## "):  parts.append(f'<h2 class="result-content" style="color:var(--cyan)">{s[3:]}</h2>')
        elif s.startswith("# "):   parts.append(f'<h1 class="result-content" style="color:var(--pink)">{s[2:]}</h1>')
        elif s.startswith("- ") or s.startswith("* "):
            parts.append(f'<div class="result-content bullet">{s[2:]}</div>')
        else:
            s2 = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color:var(--yellow)">\1</strong>', s)
            parts.append(f'<p class="result-content" style="margin:.2rem 0">{s2}</p>')
    return "".join(parts)

def err_box(msg):
    st.markdown(f'<div class="err-box">⚠&nbsp; {msg}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  CREW BUILDER
# ══════════════════════════════════════════════════════════════
def build_crew(mode, topic, llm):
    s = DuckDuckGoTool()
    if mode == "standard":
        a1=Agent(role="Research Specialist",goal="Find detailed information",backstory="Expert web researcher",llm=llm,tools=[s],verbose=True,memory=True)
        a2=Agent(role="Content Writer",goal="Write structured reports",backstory="Professional report writer",llm=llm,verbose=True,memory=True)
        a3=Agent(role="Quality Reviewer",goal="Polish the report",backstory="Expert editor",llm=llm,verbose=True,memory=True)
        t1=Task(description=f"Research comprehensively: {topic}. Facts, stats, examples.",expected_output="Detailed research notes.",agent=a1)
        t2=Task(description=f"Write report on {topic}:\n# Introduction\n## Key Concepts\n## Applications\n## Real World Examples\n## Future Scope\n## Conclusion",expected_output="Full markdown report.",agent=a2)
        t3=Task(description="Polish: fix grammar, improve clarity, ensure completeness.",expected_output="Final polished report.",agent=a3)
    elif mode == "debate":
        a1=Agent(role="Pro Debater",goal=f"Argue IN FAVOUR of: {topic}",backstory="Champion debater building strong FOR arguments.",llm=llm,tools=[s],verbose=True,memory=True)
        a2=Agent(role="Con Debater",goal=f"Argue AGAINST: {topic}",backstory="Devil's advocate finding every weakness.",llm=llm,tools=[s],verbose=True,memory=True)
        a3=Agent(role="Neutral Moderator",goal="Summarise both sides with a balanced verdict",backstory="Fair-minded moderator.",llm=llm,verbose=True,memory=True)
        t1=Task(description=f"Strongest PRO argument for {topic}:\n## Why {topic} is BENEFICIAL\n- Evidence 1\n- Evidence 2\n- Evidence 3",expected_output="PRO argument with evidence.",agent=a1)
        t2=Task(description=f"Strongest CON argument against {topic}:\n## Why {topic} is PROBLEMATIC\n- Counter 1\n- Counter 2\n- Counter 3",expected_output="CON argument with evidence.",agent=a2)
        t3=Task(description=f"Balanced debate summary:\n# Debate: {topic}\n## PRO Side\n## CON Side\n## Neutral Analysis\n## Verdict",expected_output="Balanced debate summary.",agent=a3)
    elif mode == "slides":
        a1=Agent(role="Content Researcher",goal=f"Research key points for presentation on: {topic}",backstory="Presentation content researcher.",llm=llm,tools=[s],verbose=True,memory=True)
        a2=Agent(role="Slide Architect",goal="Design complete 10-slide outline",backstory="Professional presentation designer.",llm=llm,verbose=True,memory=True)
        a3=Agent(role="Slide Reviewer",goal="Review and polish the deck",backstory="Presentation coach.",llm=llm,verbose=True,memory=True)
        t1=Task(description=f"Research key talking points for a presentation on: {topic}",expected_output="Key facts and talking points.",agent=a1)
        t2=Task(description=f"Create 10-slide outline on {topic}.\n## Slide N: [Title]\n**Key Message:** ...\n- Bullet 1\n- Bullet 2\n- Bullet 3\n**Speaker Note:** ...",expected_output="10-slide presentation outline.",agent=a2)
        t3=Task(description="Review the deck. Improve flow, speaker notes, and slide balance.",expected_output="Polished slide deck outline.",agent=a3)
    elif mode == "trends":
        a1=Agent(role="Web Trend Scout",goal=f"Find current trends about: {topic}",backstory="Expert at discovering what's trending online.",llm=llm,tools=[s],verbose=True,memory=True)
        a2=Agent(role="Data Analyst",goal="Analyse trend signals and sentiment",backstory="Analyst spotting patterns in web data.",llm=llm,tools=[s],verbose=True,memory=True)
        a3=Agent(role="Trend Reporter",goal="Write comprehensive trend analysis",backstory="Tech journalist translating trends to reports.",llm=llm,verbose=True,memory=True)
        t1=Task(description=f"Search for latest news, discussions, trending angles about: {topic}",expected_output="Current trend data.",agent=a1)
        t2=Task(description=f"Analyse trends for {topic}: top angles, sentiment, sub-topics, key events.",expected_output="Trend analysis.",agent=a2)
        t3=Task(description=f"Trend report on {topic}:\n# Trend Overview\n## Top Trending Angles\n## Sentiment Analysis\n## Emerging Sub-Topics\n## Key Events\n## Prediction & Outlook",expected_output="Full trend analysis report.",agent=a3)
    return Crew(agents=[a1,a2,a3], tasks=[t1,t2,t3], verbose=True)

# ══════════════════════════════════════════════════════════════
#  MAIN LOGIC
# ══════════════════════════════════════════════════════════════
if run:
    mode = st.session_state.mode

    if not topic.strip():
        err_box("MISSION TOPIC REQUIRED — TYPE YOUR RESEARCH TOPIC ABOVE")
    else:
        llm = LLM(
            model="openrouter/openai/gpt-3.5-turbo",
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.4,
        )
        crew = build_crew(mode, topic.strip(), llm)

        result_holder: dict = {}
        err_holder:    dict = {}

        def run_crew():
            try:    result_holder["result"] = crew.kickoff()
            except Exception as e: err_holder["error"] = str(e)

        t = threading.Thread(target=run_crew, daemon=True)
        t.start()

        terminal_ph = st.empty()
        live_ph     = st.empty()

        PHASES = {
            "standard":[(0,[],"SCOUT scanning internet databases...","PHASE 1 / 3 — WEB INTELLIGENCE"),
                        (1,[0],"SCRIBE synthesising structured report...","PHASE 2 / 3 — REPORT AUTHORING"),
                        (2,[0,1],"JUDGE polishing & finalising output...","PHASE 3 / 3 — QA REVIEW")],
            "debate":  [(0,[],"PRO building strongest arguments...","PHASE 1 / 3 — PRO CASE"),
                        (1,[0],"CON constructing counter-arguments...","PHASE 2 / 3 — CON CASE"),
                        (2,[0,1],"NEUTRAL summarising & reaching verdict...","PHASE 3 / 3 — MODERATION")],
            "slides":  [(0,[],"SCOUT researching talking points...","PHASE 1 / 3 — CONTENT RESEARCH"),
                        (1,[0],"DESIGNER architecting slide structure...","PHASE 2 / 3 — SLIDE DESIGN"),
                        (2,[0,1],"POLISH reviewing & perfecting deck...","PHASE 3 / 3 — QA REVIEW")],
            "trends":  [(0,[],"CRAWLER scanning live web for trends...","PHASE 1 / 3 — TREND DISCOVERY"),
                        (1,[0],"ANALYST processing sentiment & signals...","PHASE 2 / 3 — DATA ANALYSIS"),
                        (2,[0,1],"REPORTER writing trend analysis report...","PHASE 3 / 3 — REPORT WRITING")],
        }
        STATUSES = ["Initialising agent swarm...","Querying DuckDuckGo...","Parsing web results...",
                    "Processing data...","Generating content...","Reviewing quality...",
                    "Structuring output...","Final assembly...","Almost done..."]
        phase_data = PHASES[mode]
        dots = ["▪","▪▪","▪▪▪","▪▪▪▪"]
        pidx = tick = 0

        while t.is_alive():
            active, done_ids, pmsg, plabel = phase_data[pidx]
            show_agents(active=active, done_list=done_ids)
            dot = dots[tick % len(dots)]
            sub = STATUSES[tick % len(STATUSES)]
            terminal_ph.markdown(f"""
            <div class="terminal-box">
              <div class="terminal-phase">{plabel}</div>
              <div class="terminal-msg">{pmsg} {dot}<span class="cursor"></span></div>
              <div class="terminal-meta">MODEL: gpt-3.5-turbo &nbsp;·&nbsp; MODE: {mode.upper()} &nbsp;·&nbsp; STATUS: RUNNING</div>
              <div class="terminal-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

            if result_holder.get("result"):
                partial = str(result_holder["result"])[:500] + "…"
                live_ph.markdown(f"""
                <div class="live-out">
                  <div class="live-out-text">{partial}<span class="live-cursor"></span></div>
                </div>""", unsafe_allow_html=True)

            time.sleep(5)
            tick += 1
            if tick % 3 == 0:
                pidx = min(pidx+1, len(phase_data)-1)

        t.join()
        terminal_ph.empty()
        live_ph.empty()

        if "error" in err_holder:
            show_agents()
            err_box(f"AGENT ERROR — {err_holder['error'][:280]}")
        else:
            result     = result_holder.get("result","")
            result_str = str(result)
            for pat in [r'raw=["\'](.+?)["\'],\s*pydantic', r'raw=["\'](.+?)["\']$']:
                m = re.search(pat, result_str, re.DOTALL)
                if m: result_str = m.group(1); break

            show_agents(done_list=[0,1,2])

            st.markdown("""<div class="section-header" style="margin-top:2rem">
              <span class="section-num">04</span>
              <span class="section-title" style="color:var(--green)">Mission Output</span>
              <span class="section-line"></span>
            </div>""", unsafe_allow_html=True)

            XP = {"standard":"9,450","debate":"12,000","slides":"8,800","trends":"11,200"}
            LABELS = {"standard":"RESEARCH COMPLETE — LEVEL UP!","debate":"DEBATE CONCLUDED — VERDICT REACHED!",
                      "slides":"SLIDE DECK GENERATED!","trends":"TREND ANALYSIS COMPLETE!"}
            st.markdown(f"""
            <div class="victory-wrap">
              <div class="victory-text">🏆 {LABELS[mode]} &nbsp; +{XP[mode]} XP 🏆</div>
            </div>""", unsafe_allow_html=True)
            st.markdown('<div class="rainbow-bar"></div>', unsafe_allow_html=True)

            wc = len(result_str.split()); cc = len(result_str)
            rendered = render_html(result_str)
            MODE_LABEL = {"standard":"RESEARCH COMPLETE — LEVEL UP!","debate":"AI DEBATE — VERDICT REACHED",
                          "slides":"SLIDE DECK OUTLINE — READY TO PRESENT","trends":"LIVE TREND ANALYSIS — RESULTS"}

            st.markdown(f"""
            <div class="result-panel {mode}">
              <div class="result-panel-label">{MODE_LABEL[mode]}</div>
              <div class="result-content">{rendered}</div>
              <div class="result-meta">
                <div class="meta-chip">WORDS <span>{wc:,}</span></div>
                <div class="meta-chip">CHARS <span>{cc:,}</span></div>
                <div class="meta-chip">MODE <span>{mode.upper()}</span></div>
                <div class="meta-chip">MODEL <span>GPT-3.5-TURBO</span></div>
                <div class="meta-chip">TOPIC <span>{topic[:28]}</span></div>
                <div class="meta-chip">TIME <span>{datetime.datetime.now().strftime('%H:%M:%S')}</span></div>
              </div>
            </div>""", unsafe_allow_html=True)

            try:
                pdf_bytes = generate_pdf(result_str, topic, mode)
                FN = {"standard":"Report","debate":"Debate","slides":"Slides","trends":"Trends"}[mode]
                st.download_button(
                    label=f"⬇  DOWNLOAD GAMEIQ {FN.upper()} — PDF REPORT",
                    data=pdf_bytes,
                    file_name=f"GAMEIQ_{FN}_{topic[:20].replace(' ','_')}.pdf",
                    mime="application/pdf",
                    key="pdf_dl",
                )
            except Exception as pe:
                err_box(f"PDF ERROR — {str(pe)[:150]}")
