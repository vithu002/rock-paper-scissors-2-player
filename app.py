"""
Rock Paper Scissors — 2 Player (Local Duel)
===========================================
A local two-player Rock Paper Scissors game built with Python + Streamlit.

How a round works (the "phase" state machine):
    "p1"         -> Player 1 picks a move (hidden from Player 2)
    "p2"         -> Player 2 picks a move
    "reveal"     -> Both moves are shown, the winner gets 1 point
    "match_over" -> Someone reached the target (First to 5 mode)
    "quit"       -> The players quit; a goodbye message is shown

Run locally:   streamlit run app.py
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Game constants (Python dictionaries)
# ---------------------------------------------------------------------------

# Emoji shown for each choice
CHOICES = {
    "rock": "✊",
    "paper": "✋",
    "scissors": "✌️",
}

# Key = a move, value = the move it defeats
BEATS = {
    "rock": "scissors",      # Rock crushes Scissors
    "scissors": "paper",     # Scissors cut Paper
    "paper": "rock",         # Paper covers Rock
}

WIN_TARGET = 5  # points needed to win when "First to 5" is enabled

# Phases in which a player is allowed to make a move
MOVE_PHASES = ("p1", "p2")


# ---------------------------------------------------------------------------
# Game logic
# Every function takes a `state` argument (a dict-like object). In the app it
# is st.session_state; in the tests it is a normal Python dictionary.
# ---------------------------------------------------------------------------

def default_state():
    """Return a fresh dictionary with every value a new match needs."""
    return {
        "p1_score": 0,
        "p2_score": 0,
        "draws": 0,
        "round": 1,
        "phase": "p1",
        "p1_choice": None,
        "p2_choice": None,
        "result": None,          # "p1", "p2" or "draw" for the current round
        "match_winner": None,    # "p1" or "p2" when the match is over
        "history": [],           # list of dicts, one per finished round
    }


def initialize_game(state):
    """Create any missing keys (runs on every rerun but only fills gaps)."""
    for key, value in default_state().items():
        if key not in state:
            state[key] = value
    if "first_to_5" not in state:
        state["first_to_5"] = True


def determine_winner(choice1, choice2):
    """Return "p1", "p2" or "draw" for two choices.

    Raises ValueError if a choice is not rock, paper or scissors.
    """
    if choice1 not in CHOICES or choice2 not in CHOICES:
        raise ValueError(f"Invalid choice: {choice1!r} / {choice2!r}")
    if choice1 == choice2:
        return "draw"
    if BEATS[choice1] == choice2:
        return "p1"
    return "p2"


def check_match_winner(state):
    """If First to 5 is on and someone reached the target, end the match."""
    if not state["first_to_5"]:
        return
    if state["p1_score"] >= WIN_TARGET:
        state["match_winner"] = "p1"
        state["phase"] = "match_over"
    elif state["p2_score"] >= WIN_TARGET:
        state["match_winner"] = "p2"
        state["phase"] = "match_over"


def play_round(state, choice):
    """Register a move for whoever's turn it is.

    Returns True if the move was accepted, False if it was rejected.
    Validation here guarantees a round can only be scored ONCE:
      * moves are only accepted in the "p1" or "p2" phase
      * scoring only happens on the p2 -> reveal transition
    """
    if choice not in CHOICES:
        return False
    if state["phase"] not in MOVE_PHASES:
        return False  # round already revealed, match over or game quit

    if state["phase"] == "p1":
        # Store Player 1's secret choice and hand over to Player 2
        state["p1_choice"] = choice
        state["phase"] = "p2"
        return True

    # ---- Player 2's turn: finish the round ----
    if state["p1_choice"] is None:
        return False  # should never happen, but protects against bad state

    state["p2_choice"] = choice
    result = determine_winner(state["p1_choice"], choice)
    state["result"] = result

    # Award exactly one point (draws award nothing)
    if result == "p1":
        state["p1_score"] += 1
    elif result == "p2":
        state["p2_score"] += 1
    else:
        state["draws"] += 1

    state["history"].append({
        "round": state["round"],
        "p1": state["p1_choice"],
        "p2": choice,
        "result": result,
    })

    state["phase"] = "reveal"
    check_match_winner(state)  # may change phase to "match_over"
    return True


def next_round(state):
    """Start the next round, keeping the scores. Only valid after a reveal."""
    if state["phase"] != "reveal":
        return False
    state["round"] += 1
    state["p1_choice"] = None
    state["p2_choice"] = None
    state["result"] = None
    state["phase"] = "p1"
    return True


def reset_game(state):
    """Clear scores, choices, draws and history (keeps the First to 5 toggle)."""
    for key, value in default_state().items():
        state[key] = value


def quit_game(state):
    """End the session and show a goodbye screen."""
    state["phase"] = "quit"


def on_toggle_target(state):
    """Called when the First to 5 toggle changes."""
    if state["phase"] == "reveal":
        check_match_winner(state)
    elif state["phase"] == "match_over" and not state["first_to_5"]:
        # Target switched off after a match ended -> allow play to continue
        state["match_winner"] = None
        state["phase"] = "reveal"


# ---------------------------------------------------------------------------
# Styling (custom CSS)
# ---------------------------------------------------------------------------

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Inter:wght@400;600;800&display=swap');

:root {
  --cyan: #22d3ee;
  --orange: #fb923c;
  --panel: #0f172a;
  --border: #1e293b;
}

/* Page background */
.stApp {
  background:
    radial-gradient(circle at 15% 10%, rgba(34,211,238,0.10), transparent 40%),
    radial-gradient(circle at 85% 10%, rgba(251,146,60,0.10), transparent 40%),
    linear-gradient(180deg, #050816 0%, #0a0f1f 100%);
  color: #e2e8f0;
  font-family: 'Inter', sans-serif;
}
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1100px; padding-top: 2rem; padding-bottom: 3rem; }
#MainMenu, footer { visibility: hidden; }

/* Title */
.rps-title {
  font-family: 'Orbitron', sans-serif;
  font-weight: 900;
  text-align: center;
  font-size: clamp(1.6rem, 5vw, 3.2rem);
  line-height: 1.15;
  margin: 0;
  background: linear-gradient(90deg, var(--cyan), #f8fafc 50%, var(--orange));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.rps-subtitle {
  text-align: center;
  letter-spacing: 0.35em;
  font-size: clamp(0.62rem, 1.6vw, 0.8rem);
  color: #64748b;
  font-weight: 600;
  margin: 0.6rem 0 1.8rem 0;
}

/* Player panels */
.panel {
  background: linear-gradient(180deg, rgba(15,23,42,0.95), rgba(2,6,23,0.95));
  border: 2px solid var(--border);
  border-radius: 20px;
  padding: 1.4rem 1rem;
  text-align: center;
  transition: transform .2s ease, box-shadow .2s ease;
  margin-bottom: 1rem;
}
.panel:hover { transform: translateY(-3px); }
.panel.p1 { border-color: rgba(34,211,238,0.55); box-shadow: 0 0 30px rgba(34,211,238,0.12); }
.panel.p2 { border-color: rgba(251,146,60,0.55); box-shadow: 0 0 30px rgba(251,146,60,0.12); }
.panel.active.p1 { box-shadow: 0 0 0 3px rgba(34,211,238,0.35), 0 0 40px rgba(34,211,238,0.35); }
.panel.active.p2 { box-shadow: 0 0 0 3px rgba(251,146,60,0.35), 0 0 40px rgba(251,146,60,0.35); }
.panel.winner { animation: glow 1.2s ease-in-out infinite alternate; }
@keyframes glow { from { filter: brightness(1); } to { filter: brightness(1.25); } }

.panel-label {
  font-family: 'Orbitron', sans-serif;
  font-weight: 800;
  letter-spacing: 0.15em;
  font-size: 1rem;
}
.p1 .panel-label, .p1 .score { color: var(--cyan); }
.p2 .panel-label, .p2 .score { color: var(--orange); }

.choice-box {
  width: 120px; height: 120px;
  margin: 1rem auto;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 3.6rem;
  background: #020617;
  border: 2px dashed #334155;
}
.p1 .choice-box.revealed { border: 2px solid var(--cyan); }
.p2 .choice-box.revealed { border: 2px solid var(--orange); }
.choice-box .q { font-family: 'Orbitron', sans-serif; color: #475569; font-weight: 900; }
.choice-name { font-size: .8rem; color: #94a3b8; letter-spacing: .2em; min-height: 1.2em; }
.score {
  font-family: 'Orbitron', sans-serif;
  font-size: clamp(3rem, 8vw, 4.5rem);
  font-weight: 900;
  line-height: 1;
  margin-top: .6rem;
}
.score-label { font-size: .7rem; color: #64748b; letter-spacing: .3em; }

/* Centre stats */
.stats { display: flex; flex-direction: column; gap: .7rem; margin-bottom: 1rem; }
.stat {
  background: rgba(15,23,42,0.8);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: .7rem;
  text-align: center;
}
.stat .v { font-family: 'Orbitron', sans-serif; font-size: 1.6rem; font-weight: 800; color: #f8fafc; }
.stat .k { font-size: .65rem; letter-spacing: .25em; color: #64748b; }
.vs {
  font-family: 'Orbitron', sans-serif; font-weight: 900; text-align: center;
  font-size: 1.4rem; color: #475569; letter-spacing: .2em;
}

/* Status banner */
.banner {
  text-align: center;
  border-radius: 14px;
  padding: .9rem 1rem;
  font-weight: 800;
  font-size: clamp(1rem, 2.6vw, 1.25rem);
  margin: .4rem 0 1.2rem 0;
  border: 1px solid var(--border);
  background: rgba(15,23,42,0.85);
}
.banner.p1 { color: var(--cyan); border-color: rgba(34,211,238,.5); }
.banner.p2 { color: var(--orange); border-color: rgba(251,146,60,.5); }
.banner.draw { color: #e2e8f0; }
.banner.match { font-family: 'Orbitron', sans-serif; font-size: clamp(1.1rem, 3vw, 1.6rem);
  background: linear-gradient(90deg, rgba(34,211,238,.15), rgba(251,146,60,.15)); color: #fde68a; border-color: #fde68a; }

/* All Streamlit buttons */
.stButton > button {
  width: 100%;
  border-radius: 14px;
  font-weight: 800;
  border: 1px solid #334155;
  background: #111827;
  color: #e2e8f0;
  transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
}
.stButton > button:hover { transform: translateY(-2px); filter: brightness(1.15); border-color: #64748b; color: #fff; }
.stButton > button:active { transform: translateY(0); }
.stButton > button:disabled { opacity: .4; transform: none; }

/* Big Rock / Paper / Scissors buttons (Streamlit adds .st-key-<key>) */
.st-key-btn_rock button, .st-key-btn_paper button, .st-key-btn_scissors button {
  min-height: 110px;
  font-size: 1.5rem;
  color: #fff;
  border: none;
}
.st-key-btn_rock button p, .st-key-btn_paper button p, .st-key-btn_scissors button p { font-size: 1.4rem; font-weight: 800; }
.st-key-btn_rock button     { background: linear-gradient(135deg, #16a34a, #15803d); box-shadow: 0 8px 24px rgba(22,163,74,.35); }
.st-key-btn_paper button    { background: linear-gradient(135deg, #2563eb, #1d4ed8); box-shadow: 0 8px 24px rgba(37,99,235,.35); }
.st-key-btn_scissors button { background: linear-gradient(135deg, #dc2626, #b91c1c); box-shadow: 0 8px 24px rgba(220,38,38,.35); }
.st-key-btn_rock button:hover, .st-key-btn_paper button:hover, .st-key-btn_scissors button:hover { color: #fff; border: none; }

/* Control buttons */
.st-key-btn_next button  { border-color: var(--cyan); color: var(--cyan); }
.st-key-btn_reset button { border-color: #fbbf24; color: #fbbf24; }
.st-key-btn_quit button  { border-color: #f87171; color: #f87171; }

.hint { text-align: center; color: #94a3b8; font-size: .85rem; margin: .3rem 0 1rem; }
.goodbye { text-align: center; padding: 2.5rem 1rem; }
.goodbye .big { font-size: 4rem; }

/* Toggle label colour */
[data-testid="stWidgetLabel"] p, .stToggle label p { color: #cbd5e1 !important; }
[data-testid="stExpander"] { background: rgba(15,23,42,.7); border-radius: 14px; border: 1px solid var(--border); }

/* Mobile tweaks: Streamlit stacks columns automatically below ~640px */
@media (max-width: 640px) {
  .choice-box { width: 96px; height: 96px; font-size: 2.8rem; }
  .st-key-btn_rock button, .st-key-btn_paper button, .st-key-btn_scissors button { min-height: 72px; }
  .rps-subtitle { letter-spacing: .2em; }
}
</style>
"""


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def player_panel(state, player):
    """Return the HTML for one player's panel ("p1" or "p2")."""
    name = "PLAYER 1" if player == "p1" else "PLAYER 2"
    score = state[f"{player}_score"]
    choice = state[f"{player}_choice"]
    phase = state["phase"]

    # Choices are only shown once BOTH players have picked (reveal / match over)
    revealed = phase in ("reveal", "match_over") and choice is not None

    if revealed:
        inner = CHOICES[choice]
        caption = choice.upper()
        box_class = "choice-box revealed"
    else:
        inner = '<span class="q">?</span>'
        # Show "LOCKED IN" (never the actual move) once a player has chosen
        caption = "LOCKED IN ✔" if choice is not None else ("CHOOSING…" if phase == player else "")
        box_class = "choice-box"

    classes = ["panel", player]
    if phase == player:
        classes.append("active")
    if state["match_winner"] == player or (phase == "reveal" and state["result"] == player):
        classes.append("winner")

    return f"""
    <div class="{' '.join(classes)}">
      <div class="panel-label">{name}</div>
      <div class="{box_class}">{inner}</div>
      <div class="choice-name">{caption}</div>
      <div class="score">{score}</div>
      <div class="score-label">SCORE</div>
    </div>
    """


def stats_html(state):
    target = WIN_TARGET if state["first_to_5"] else "∞"
    return f"""
    <div class="vs">VS</div>
    <div class="stats">
      <div class="stat"><div class="v">{state['round']}</div><div class="k">ROUND</div></div>
      <div class="stat"><div class="v">{state['draws']}</div><div class="k">DRAWS</div></div>
      <div class="stat"><div class="v">{target}</div><div class="k">TARGET</div></div>
    </div>
    """


def banner_html(state):
    """Status message that tells the players what is happening."""
    phase = state["phase"]
    if phase == "p1":
        return '<div class="banner p1">🎮 Player 1, your turn — pick secretly!</div>'
    if phase == "p2":
        return ('<div class="banner p2">🎮 Player 2, your turn — '
                'Player 1 has locked in!</div>')
    if phase == "match_over":
        who = "PLAYER 1" if state["match_winner"] == "p1" else "PLAYER 2"
        return f'<div class="banner match">🏆 {who} WINS THE MATCH! 🏆</div>'
    # phase == "reveal"
    result = state["result"]
    p1, p2 = state["p1_choice"], state["p2_choice"]
    if result == "draw":
        return f'<div class="banner draw">🤝 Draw! Both chose {p1.title()} {CHOICES[p1]}</div>'
    winner_choice, loser_choice = (p1, p2) if result == "p1" else (p2, p1)
    who = "Player 1" if result == "p1" else "Player 2"
    return (f'<div class="banner {result}">🎉 {who} wins the round! '
            f'{winner_choice.title()} {CHOICES[winner_choice]} beats '
            f'{loser_choice.title()} {CHOICES[loser_choice]}</div>')


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="Rock Paper Scissors — 2 Player",
                       page_icon="✊", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)

    state = st.session_state
    initialize_game(state)

    st.markdown('<h1 class="rps-title">Rock Paper Scissors — 2 Player</h1>',
                unsafe_allow_html=True)
    st.markdown('<p class="rps-subtitle">LOCAL DUEL · 2 PLAYERS · 1 DEVICE</p>',
                unsafe_allow_html=True)

    # ---- Quit screen ----
    if state["phase"] == "quit":
        p1, p2 = state["p1_score"], state["p2_score"]
        if p1 > p2:
            summary = f"Player 1 finished ahead, {p1} – {p2}."
        elif p2 > p1:
            summary = f"Player 2 finished ahead, {p2} – {p1}."
        else:
            summary = f"It ended all square at {p1} – {p2}."
        st.markdown(f"""
        <div class="panel goodbye">
          <div class="big">👋</div>
          <h2 style="font-family:Orbitron,sans-serif;color:#f8fafc;">Thanks for playing!</h2>
          <p style="color:#94a3b8;">{summary} Rounds played: {len(state['history'])} · Draws: {state['draws']}</p>
          <p style="color:#64748b;">See you next duel.</p>
        </div>""", unsafe_allow_html=True)
        st.button("🔄 Start a New Game", key="btn_restart",
                  on_click=reset_game, args=(state,), width="stretch")
        return

    # ---- Scoreboard: P1 | stats | P2 ----
    col1, col_mid, col2 = st.columns([5, 3, 5])
    with col1:
        st.markdown(player_panel(state, "p1"), unsafe_allow_html=True)
    with col_mid:
        st.markdown(stats_html(state), unsafe_allow_html=True)
    with col2:
        st.markdown(player_panel(state, "p2"), unsafe_allow_html=True)

    st.markdown(banner_html(state), unsafe_allow_html=True)

    # ---- Move buttons (only visible while a player needs to choose) ----
    if state["phase"] in MOVE_PHASES:
        if state["phase"] == "p2":
            st.markdown('<p class="hint">Player 1: look away! Player 2: make your pick.</p>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<p class="hint">Player 2: look away while Player 1 chooses.</p>',
                        unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        for column, choice in zip((b1, b2, b3), CHOICES):
            with column:
                st.button(f"{CHOICES[choice]}  {choice.title()}",
                          key=f"btn_{choice}", on_click=play_round,
                          args=(state, choice), width="stretch")

    # ---- Controls ----
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("▶ Next Round", key="btn_next", on_click=next_round, args=(state,),
                  disabled=state["phase"] != "reveal", width="stretch")
    with c2:
        label = "🔄 New Match" if state["phase"] == "match_over" else "🔄 Reset Game"
        st.button(label, key="btn_reset", on_click=reset_game, args=(state,),
                  width="stretch")
    with c3:
        st.button("⏻ Quit Game", key="btn_quit", on_click=quit_game, args=(state,),
                  width="stretch")

    st.toggle(f"🏁 First to {WIN_TARGET}", key="first_to_5",
              on_change=on_toggle_target, args=(state,))

    # ---- Round history ----
    if state["history"]:
        with st.expander(f"📜 Round history ({len(state['history'])})"):
            names = {"p1": "Player 1", "p2": "Player 2", "draw": "Draw"}
            for item in reversed(state["history"]):
                st.markdown(
                    f"**Round {item['round']}** — P1 {CHOICES[item['p1']]} vs "
                    f"{CHOICES[item['p2']]} P2 → **{names[item['result']]}**")


if __name__ == "__main__":
    main()
