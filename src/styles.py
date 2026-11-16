"""Global visual system for AirSense."""

APP_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@300..700&display=swap');

:root {
    --ink: #0B1516;
    --ink-2: #102021;
    --ink-3: #162A2B;
    --panel: rgba(20, 37, 37, .84);
    --panel-soft: rgba(255, 255, 255, .035);
    --cream: #F3F0E7;
    --muted: #A2ACA3;
    --muted-2: #738078;
    --coral: #C9795E;
    --coral-soft: #B96C55;
    --cyan: #86B9A5;
    --amber: #D4B06B;
    --line: rgba(243, 240, 231, .10);
    --line-soft: rgba(243, 240, 231, .06);
    --display: 'Fraunces', Georgia, serif;
    --body: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
    --mono: 'JetBrains Mono', ui-monospace, monospace;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
    background: var(--ink) !important;
    color: var(--cream) !important;
    font-family: var(--body);
}

[data-testid="stAppViewContainer"] {
    position: relative;
    isolation: isolate;
}

/* Fallback atmosphere behind the canvas layer. */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: -25%;
    z-index: 0;
    pointer-events: none;
    background:
        radial-gradient(38% 46% at 18% 18%, rgba(75, 133, 118, .22), transparent 68%),
        radial-gradient(34% 40% at 82% 28%, rgba(185, 108, 79, .13), transparent 70%),
        radial-gradient(42% 50% at 55% 92%, rgba(78, 103, 128, .16), transparent 70%),
        linear-gradient(180deg, #0B1516 0%, #0D1A1B 55%, #091112 100%);
    filter: blur(14px);
    animation: auraDrift 26s ease-in-out infinite alternate;
}

@keyframes auraDrift {
    0%   { transform: translate3d(-1.5%, -1%, 0) scale(1); }
    50%  { transform: translate3d(1.5%, 1%, 0) scale(1.04); }
    100% { transform: translate3d(-1%, 2%, 0) scale(1.02); }
}

[data-testid="stHeader"] {
    background: transparent !important;
    backdrop-filter: none !important;
}

/* Keep the toolbar container: in Streamlit 1.50 it also holds the control that
   reopens a collapsed sidebar. Hide only the deploy/status chrome. */
[data-testid="stToolbar"] {
    z-index: 20 !important;
}
[data-testid="stStatusWidget"],
[data-testid="stAppDeployButton"],
[data-testid="stToolbar"] .stDeployButton,
[data-testid="stBaseButton-header"] {
    display: none !important;
}
[data-testid="stExpandSidebarButton"] button,
[data-testid="stExpandSidebarButton"] {
    color: var(--cream) !important;
}

#MainMenu, footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

[data-testid="stMain"] {
    position: relative !important;
    z-index: 1 !important;
    background: transparent !important;
}

[data-testid="stMainBlockContainer"] {
    position: relative;
    z-index: 1;
    max-width: 1380px;
    padding: 1.4rem 2.2rem 3.2rem 2.2rem;
}

[data-testid="stSidebar"] {
    z-index: 3 !important;
    min-width: 306px !important;
    background: linear-gradient(180deg, rgba(6, 11, 18, .98), rgba(9, 17, 26, .99)) !important;
    border-right: 1px solid var(--line);
    box-shadow: 24px 0 80px rgba(0, 0, 0, .35);
}

/* Streamlit animates to max-width:0 with a transform based on its native 199px
   width. Our wider sidebar needs to collapse cleanly instead of leaving a slice. */
[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 0 !important;
    transform: translateX(-306px) !important;
    border-right-color: transparent;
}
[data-testid="stSidebar"][aria-expanded="true"] {
    min-width: 306px !important;
    transform: none !important;
}

[data-testid="stSidebarUserContent"] {
    padding: 1.1rem 1.15rem 2.4rem 1.15rem;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
}



[data-testid="stSidebar"] * { color: var(--cream); }

[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stCaption {
    color: var(--muted) !important;
}

[data-testid="stSidebar"] hr {
    border-color: var(--line) !important;
    margin: 1rem 0;
}

h1, h2, h3 {
    font-family: var(--display) !important;
    font-weight: 500 !important;
    letter-spacing: -.035em !important;
    color: var(--cream) !important;
}

h4 {
    font-family: var(--body) !important;
    font-weight: 650 !important;
    letter-spacing: -.02em !important;
    color: var(--cream) !important;
}

p, label, li, .stMarkdown { color: var(--cream); }

[data-testid="stMarkdownContainer"] p { line-height: 1.72; }

a { color: var(--cyan); text-decoration: none; border-bottom: 1px solid rgba(111, 227, 214, .25); }
a:hover { color: var(--cream); border-color: var(--cream); }

small, .stCaption, [data-testid="stCaptionContainer"] {
    color: var(--muted) !important;
}

hr { border-color: var(--line) !important; }

/* ---------------------------------------------------------------- widgets */

[data-testid="stMain"] a {
    color: var(--cyan) !important;
    text-decoration-color: rgba(111, 227, 214, .35) !important;
}
[data-testid="stMain"] a:hover { color: var(--cream) !important; }

[data-testid="stMetricLabel"] p {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    line-height: 1.35 !important;
}
[data-testid="stMetricValue"] {
    font-size: clamp(1.35rem, 3vw, 2.1rem) !important;
}
[data-testid="stMetricValue"] div {
    overflow: visible !important;
    text-overflow: clip !important;
}

.stButton > button, .stDownloadButton > button {
    font-family: var(--body);
    font-weight: 600;
    font-size: .82rem;
    color: var(--cream);
    background: rgba(255, 255, 255, .035);
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: .55rem 1.05rem;
    min-height: 2.45rem;
    white-space: nowrap;
    transition: transform .18s ease, border-color .18s ease, background .18s ease, color .18s ease, box-shadow .18s ease;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px);
    border-color: rgba(255, 128, 105, .55);
    background: rgba(255, 128, 105, .09);
    color: var(--coral);
    box-shadow: 0 12px 30px rgba(0, 0, 0, .25);
}

.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    color: #11201F;
    background: linear-gradient(135deg, #D98C70, #B96C55);
    border: 1px solid transparent;
    box-shadow: 0 12px 34px rgba(241, 132, 112, .22);
}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {
    color: #0E1A1A;
    background: linear-gradient(135deg, #E5A084, #C9795E);
    box-shadow: 0 16px 42px rgba(241, 132, 112, .32);
}

.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: rgba(255, 255, 255, .04) !important;
    color: var(--cream) !important;
    border: 1px solid var(--line) !important;
    border-radius: 13px !important;
    font-family: var(--body) !important;
    font-size: .88rem !important;
    padding: .65rem .8rem !important;
    transition: border-color .18s ease, box-shadow .18s ease;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: rgba(111, 227, 214, .55) !important;
    box-shadow: 0 0 0 3px rgba(111, 227, 214, .10) !important;
}

[data-baseweb="select"] > div {
    background: rgba(255, 255, 255, .04) !important;
    border-color: var(--line) !important;
    border-radius: 13px !important;
    color: var(--cream) !important;
    font-family: var(--body) !important;
    font-size: .86rem !important;
}

[data-baseweb="select"] svg { fill: var(--muted) !important; }

[data-baseweb="popover"] [data-baseweb="menu"] {
    background: #0E1925 !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
}
[data-baseweb="popover"] li { color: var(--cream) !important; font-family: var(--body) !important; }
[data-baseweb="popover"] li:hover { background: rgba(111, 227, 214, .10) !important; }

.stSlider [data-baseweb="slider"] [role="slider"] {
    background: var(--coral) !important;
    border-color: var(--coral) !important;
    box-shadow: 0 0 0 4px rgba(255, 128, 105, .14) !important;
}
.stSlider [data-baseweb="slider"] > div > div { background: var(--coral) !important; }
.stSlider [data-baseweb="slider"] > div { background: rgba(255, 255, 255, .10) !important; }

.stPills [data-testid="stButtonGroup"] button,
[data-testid="stPills"] button,
[data-testid="stButtonGroup"] button {
    background: rgba(255, 255, 255, .03);
    border: 1px solid var(--line);
    border-radius: 999px;
    color: var(--muted);
    font-family: var(--mono);
    font-size: 9.5px;
    letter-spacing: .06em;
    text-transform: uppercase;
    padding: .3rem .6rem;
    min-height: 1.9rem;
}
[data-testid="stButtonGroup"] button[aria-checked="true"],
[data-testid="stPills"] button[aria-checked="true"] {
    background: rgba(111, 227, 214, .12);
    border-color: rgba(111, 227, 214, .45);
    color: var(--cyan);
}

[data-testid="stWidgetLabel"] p {
    font-family: var(--mono) !important;
    font-size: 9px !important;
    letter-spacing: .13em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
}

/* ------------------------------------------------------------------ tabs */

.stTabs [data-baseweb="tab-list"] {
    gap: .25rem;
    background: rgba(255, 255, 255, .03);
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: .3rem;
    width: fit-content;
    max-width: 100%;
    overflow-x: auto;
    scrollbar-width: none;
    margin-bottom: .4rem;
}
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }

.stTabs [data-baseweb="tab"] {
    height: auto;
    min-height: 2.1rem;
    padding: .48rem .9rem;
    border-radius: 999px;
    color: var(--muted);
    background: transparent;
    font-family: var(--mono);
    font-size: 9.5px;
    font-weight: 500;
    letter-spacing: .09em;
    text-transform: uppercase;
    transition: color .18s ease, background .18s ease;
}
.stTabs [data-baseweb="tab"] p {
    font-family: var(--mono) !important;
    font-size: 9.5px !important;
    font-weight: 500 !important;
    letter-spacing: .09em !important;
    text-transform: uppercase !important;
    line-height: 1.2 !important;
    color: inherit !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--cream); background: rgba(255, 255, 255, .04); }
.stTabs [aria-selected="true"] {
    color: #0A121C !important;
    background: var(--cream) !important;
}
.stTabs [aria-selected="true"] p,
.stTabs [aria-selected="true"] * {
    color: #0A121C !important;
    -webkit-text-fill-color: #0A121C !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.6rem; }

/* --------------------------------------------------------------- elements */

[data-testid="stMetric"] {
    background: linear-gradient(150deg, rgba(20, 35, 49, .88), rgba(10, 18, 28, .80));
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1rem 1.1rem .9rem 1.1rem;
    transition: transform .2s ease, border-color .2s ease;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); border-color: rgba(111, 227, 214, .28); }
[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-family: var(--mono) !important;
    font-size: 9px !important;
    letter-spacing: .13em;
    text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    color: var(--cream) !important;
    font-family: var(--display) !important;
    font-weight: 500 !important;
    letter-spacing: -.03em;
}
[data-testid="stMetricDelta"] { font-family: var(--mono); font-size: 10px; }

[data-testid="stDataFrame"] {
    border: 1px solid var(--line);
    border-radius: 16px;
    overflow: hidden;
}

[data-testid="stExpander"] details {
    background: rgba(255, 255, 255, .028);
    border: 1px solid var(--line) !important;
    border-radius: 16px !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    font-family: var(--body);
    font-weight: 600;
    font-size: .88rem;
    color: var(--cream);
}
[data-testid="stExpander"] summary:hover { color: var(--cyan); }

[data-testid="stAlert"] {
    background: rgba(255, 255, 255, .035);
    border: 1px solid var(--line);
    border-left: 2px solid var(--cyan);
    border-radius: 14px;
    color: var(--cream);
}
[data-testid="stAlert"] p { color: var(--cream); }

[data-testid="stVegaLiteChart"] {
    background: linear-gradient(155deg, rgba(17, 30, 43, .72), rgba(8, 15, 24, .55));
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 1rem 1rem .6rem 1rem;
}

[data-testid="stChatMessage"] {
    background: rgba(255, 255, 255, .032);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: .8rem .95rem;
}
[data-testid="stChatMessage"] p { line-height: 1.7; }

[data-testid="stChatInput"] {
    background: rgba(255, 255, 255, .04);
    border: 1px solid var(--line);
    border-radius: 16px;
}
[data-testid="stChatInput"] textarea { color: var(--cream) !important; font-family: var(--body) !important; }

.stSpinner > div { border-top-color: var(--cyan) !important; }

.stCheckbox [data-baseweb="checkbox"] span[aria-checked="true"] {
    background: var(--coral) !important;
    border-color: var(--coral) !important;
}

/* --------------------------------------------------------------- top bar */

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: .55rem 0 1.05rem 0;
    border-bottom: 1px solid var(--line);
    margin-bottom: .4rem;
    flex-wrap: wrap;
}
.topbar-brand { display: flex; align-items: center; gap: .65rem; }
.topbar-slash { color: var(--muted-2); font-family: var(--mono); font-size: 11px; }
.topbar-sub {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: .16em;
    text-transform: uppercase;
    color: var(--muted);
}
.topbar-right { display: flex; align-items: center; gap: .85rem; flex-wrap: wrap; }
.topbar-place {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: .06em;
    color: var(--cream);
}
.topbar-country { color: var(--muted); }

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: .3rem .62rem;
    font-family: var(--mono);
    font-size: 8.5px;
    letter-spacing: .15em;
    color: var(--muted);
    background: rgba(255, 255, 255, .025);
}
.status-pill.live { color: var(--cyan); border-color: rgba(111, 227, 214, .25); background: rgba(111, 227, 214, .055); }
.status-pill.demo { color: var(--amber); border-color: rgba(233, 187, 120, .3); background: rgba(233, 187, 120, .07); }

.pulse {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    box-shadow: 0 0 0 0 currentColor;
    animation: pulseRing 2.4s ease-out infinite;
}
@keyframes pulseRing {
    0%   { box-shadow: 0 0 0 0 rgba(111, 227, 214, .35); }
    70%  { box-shadow: 0 0 0 7px rgba(111, 227, 214, 0); }
    100% { box-shadow: 0 0 0 0 rgba(111, 227, 214, 0); }
}

/* ------------------------------------------------------------------- hero */

.hero-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.12fr) minmax(360px, .88fr);
    gap: clamp(1.6rem, 4vw, 3.4rem);
    align-items: center;
    padding: clamp(1.8rem, 4vw, 3.4rem) 0 clamp(1.2rem, 3vw, 2rem) 0;
}

.eyebrow {
    display: flex;
    align-items: center;
    gap: .7rem;
    color: var(--cyan);
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: .2em;
    text-transform: uppercase;
    margin-bottom: .9rem;
}
.eyebrow::before {
    content: "";
    width: 26px;
    height: 1px;
    background: linear-gradient(90deg, var(--cyan), transparent);
}

.hero-title {
    font-family: var(--display) !important;
    font-size: clamp(3.4rem, 7.4vw, 7.1rem);
    line-height: .9;
    font-weight: 400 !important;
    letter-spacing: -.06em !important;
    color: var(--cream);
    margin: 0;
    text-wrap: balance;
}
.hero-title em {
    font-style: italic;
    font-weight: 400;
    color: var(--coral);
    background: linear-gradient(105deg, #D99678 0%, #C9795E 45%, #D4B06B 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-lede {
    max-width: 36rem;
    margin-top: 1.25rem;
    color: #B3C0CC;
    font-size: clamp(.96rem, 1.15vw, 1.06rem);
    line-height: 1.78;
}
.hero-lede b { color: var(--cream); font-weight: 600; }

.hero-meta {
    display: flex;
    flex-wrap: wrap;
    gap: .55rem;
    margin-top: 1.5rem;
}
.hero-chip {
    border: 1px solid var(--line);
    background: rgba(255, 255, 255, .028);
    border-radius: 999px;
    padding: .38rem .7rem;
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: .08em;
    color: var(--muted);
}
.hero-chip strong { color: var(--cream); font-weight: 500; }
.hero-chip.accent { border-color: rgba(111, 227, 214, .25); color: var(--cyan); background: rgba(111, 227, 214, .045); }

.hero-coord {
    margin-top: 1.35rem;
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: .12em;
    color: var(--muted-2);
    display: flex;
    align-items: center;
    gap: .6rem;
}
.hero-coord::before { content: "◌"; color: var(--cyan); font-size: 12px; }

/* ------------------------------------------------------------------ gauge */

.gauge-card {
    position: relative;
    border: 1px solid rgba(244, 237, 224, .11);
    border-radius: 26px;
    padding: 1.05rem 1.25rem 1.1rem 1.25rem;
    background:
        radial-gradient(120% 95% at 50% 0%, rgba(var(--accent-rgb), .13), transparent 58%),
        linear-gradient(160deg, rgba(19, 34, 48, .94), rgba(8, 15, 24, .96));
    box-shadow: 0 34px 90px rgba(0, 0, 0, .42), inset 0 1px 0 rgba(255, 255, 255, .06);
    overflow: hidden;
}
.gauge-card::after {
    content: "";
    position: absolute;
    width: 240px;
    height: 240px;
    top: -110px;
    right: -80px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(var(--accent-rgb), .18), transparent 70%);
    pointer-events: none;
}
.gauge-top { display: flex; align-items: center; justify-content: space-between; gap: .8rem; position: relative; z-index: 1; }
.live-chip {
    display: inline-flex;
    align-items: center;
    gap: .42rem;
    font-family: var(--mono);
    font-size: 8px;
    letter-spacing: .16em;
    color: var(--accent);
}
.gauge-time { font-family: var(--mono); font-size: 9px; color: var(--muted); letter-spacing: .04em; }
.gauge-shell { position: relative; width: 100%; max-width: 330px; margin: .15rem auto 0 auto; }
.gauge-shell svg,
.gauge-shell .gauge-svg { display: block; width: 100%; height: auto; overflow: visible; }
.gauge-readout {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding-top: 1.4rem;
    pointer-events: none;
}
.gauge-kicker { font-family: var(--mono); font-size: 8px; letter-spacing: .2em; color: var(--muted); }
.gauge-number {
    font-family: var(--display);
    font-size: clamp(3.4rem, 5vw, 4.5rem);
    font-weight: 450;
    line-height: 1;
    letter-spacing: -.05em;
    margin: .05rem 0 .15rem 0;
}
.gauge-cat {
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: .13em;
    text-transform: uppercase;
    color: var(--cream);
    opacity: .78;
    text-align: center;
    max-width: 12rem;
}

.aqi-scale { margin-top: -.6rem; position: relative; z-index: 1; }
.scale-track {
    position: relative;
    display: flex;
    height: 5px;
    border-radius: 999px;
    overflow: visible;
}
.scale-segment { height: 5px; display: block; }
.scale-segment:first-child { border-radius: 999px 0 0 999px; }
.scale-segment:last-child { border-radius: 0 999px 999px 0; }
.scale-marker {
    position: absolute;
    top: 50%;
    width: 2px;
    height: 14px;
    background: var(--cream);
    border-radius: 2px;
    transform: translate(-50%, -50%);
    box-shadow: 0 0 10px rgba(244, 237, 224, .8);
}
.scale-labels {
    display: flex;
    justify-content: space-between;
    margin-top: .42rem;
    font-family: var(--mono);
    font-size: 7.5px;
    letter-spacing: .08em;
    color: var(--muted-2);
}
.gauge-foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: .7rem;
    border-top: 1px solid var(--line-soft);
    margin-top: .85rem;
    padding-top: .75rem;
    position: relative;
    z-index: 1;
}
.gauge-source { font-family: var(--mono); font-size: 8px; letter-spacing: .04em; color: var(--muted-2); }
.trend-chip {
    font-family: var(--mono);
    font-size: 8px;
    letter-spacing: .04em;
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: .25rem .5rem;
    color: var(--muted);
    white-space: nowrap;
}
.trend-chip.up { color: var(--coral); border-color: rgba(255, 128, 105, .3); background: rgba(255, 128, 105, .07); }
.trend-chip.down { color: var(--cyan); border-color: rgba(111, 227, 214, .3); background: rgba(111, 227, 214, .07); }

/* -------------------------------------------------------------------- kpi */

.kpi-card {
    position: relative;
    height: 100%;
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: .95rem 1rem .75rem 1rem;
    background: linear-gradient(155deg, rgba(19, 33, 47, .78), rgba(9, 16, 25, .62));
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, .035);
    transition: transform .22s ease, border-color .22s ease, box-shadow .22s ease;
    overflow: hidden;
}
.kpi-card::before {
    content: "";
    position: absolute;
    left: 0; right: 0; top: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: .55;
}
.kpi-card:hover {
    transform: translateY(-3px);
    border-color: rgba(244, 237, 224, .18);
    box-shadow: 0 18px 40px rgba(0, 0, 0, .22);
}
.kpi-top { display: flex; align-items: center; justify-content: space-between; gap: .4rem; }
.kpi-label { font-family: var(--mono); font-size: 9px; letter-spacing: .12em; color: var(--muted); }
.kpi-ratio {
    font-family: var(--mono);
    font-size: 7.5px;
    letter-spacing: .04em;
    border: 1px solid;
    border-radius: 999px;
    padding: .18rem .38rem;
    white-space: nowrap;
}
.kpi-main { display: flex; align-items: baseline; gap: .35rem; margin-top: .45rem; }
.kpi-value {
    font-family: var(--display);
    font-size: clamp(1.75rem, 2.6vw, 2.5rem);
    font-weight: 450;
    letter-spacing: -.04em;
    line-height: 1;
}
.kpi-unit { font-family: var(--mono); font-size: 8.5px; color: var(--muted-2); }
.spark { width: 100%; height: 34px; margin-top: .5rem; display: block; object-fit: contain; object-position: left center; }
.kpi-foot { font-family: var(--mono); font-size: 7.5px; color: var(--muted-2); letter-spacing: .03em; margin-top: .15rem; }

/* ------------------------------------------------------------------ cards */

.section-head { margin: 1.2rem 0 .2rem 0; }
.section-heading {
    font-family: var(--display) !important;
    font-size: clamp(1.7rem, 2.5vw, 2.35rem);
    font-weight: 450 !important;
    letter-spacing: -.045em !important;
    line-height: 1.05;
    margin: 0 0 .45rem 0;
}
.section-copy { color: var(--muted); font-size: .9rem; max-width: 49rem; margin: 0 0 .8rem 0; line-height: 1.7; }

.glass-card {
    position: relative;
    height: 100%;
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 1.25rem 1.4rem;
    background: linear-gradient(150deg, rgba(19, 33, 47, .82), rgba(9, 16, 25, .72));
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, .035), 0 18px 50px rgba(0, 0, 0, .12);
    overflow: hidden;
}
.card-topline { display: flex; align-items: center; justify-content: space-between; gap: .8rem; flex-wrap: wrap; }
.card-kicker { font-family: var(--mono); font-size: 8.5px; letter-spacing: .17em; color: var(--muted); }
.mono-chip {
    font-family: var(--mono);
    font-size: 7.5px;
    letter-spacing: .1em;
    color: var(--muted-2);
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: .2rem .45rem;
}
.card-source {
    margin-top: 1rem;
    padding-top: .75rem;
    border-top: 1px solid var(--line-soft);
    font-family: var(--mono);
    font-size: 7.5px;
    line-height: 1.65;
    letter-spacing: .02em;
    color: var(--muted-2);
}
.band-badge {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    font-family: var(--mono);
    font-size: 8px;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--accent);
    border: 1px solid rgba(var(--accent-rgb), .3);
    background: rgba(var(--accent-rgb), .08);
    border-radius: 999px;
    padding: .28rem .58rem;
}
.band-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); }
.mini-label { font-family: var(--mono); font-size: 7.5px; letter-spacing: .16em; color: var(--muted-2); }
.empty-copy { color: var(--muted); font-size: .85rem; line-height: 1.7; }

.health-card {
    border-top: 2px solid var(--accent);
    background:
        radial-gradient(120% 110% at 0% 0%, rgba(var(--accent-rgb), .13), transparent 55%),
        linear-gradient(150deg, rgba(19, 33, 47, .86), rgba(9, 16, 25, .74));
}
.health-headline { display: flex; align-items: baseline; gap: .55rem; margin-top: 1.1rem; }
.health-value { font-family: var(--display); font-size: 3.2rem; line-height: .95; letter-spacing: -.05em; color: var(--accent); }
.health-unit { font-family: var(--mono); font-size: 9px; letter-spacing: .12em; color: var(--muted); }
.health-copy { margin-top: .85rem; color: #C6D0DA; font-size: .88rem; line-height: 1.72; }
.health-divider { height: 1px; background: var(--line-soft); margin: 1rem 0 .9rem 0; }
.health-sensitive p { margin-top: .35rem; color: var(--muted); font-size: .82rem; line-height: 1.68; }

.load-list { margin-top: 1.15rem; display: flex; flex-direction: column; gap: .85rem; }
.load-head { display: grid; grid-template-columns: 1fr auto auto; gap: .6rem; align-items: baseline; }
.load-name { font-size: .82rem; font-weight: 600; color: var(--cream); }
.load-value { font-family: var(--mono); font-size: .74rem; color: var(--cream); }
.load-unit { color: var(--muted-2); font-size: .6rem; }
.load-ratio { font-family: var(--mono); font-size: .68rem; }
.load-track { position: relative; height: 4px; background: rgba(255, 255, 255, .06); border-radius: 999px; margin-top: .35rem; overflow: visible; }
.load-fill { display: block; height: 4px; border-radius: 999px; }
.load-tick { position: absolute; left: 25%; top: -2px; width: 1px; height: 8px; background: rgba(244, 237, 224, .35); }
.dominant-note { margin-top: 1.1rem; padding: .8rem .9rem; border: 1px solid var(--line); border-radius: 14px; background: rgba(255, 255, 255, .025); }
.dominant-note p { margin-top: .3rem; font-size: .78rem; line-height: 1.6; color: var(--muted); }

/* ----------------------------------------------------------- who / charts */

.who-card { padding-bottom: .9rem; }
.who-head {
    display: grid;
    grid-template-columns: 1.05fr 2fr .85fr .85fr .4fr;
    gap: .8rem;
    margin: 1.1rem 0 .35rem 0;
    padding-bottom: .45rem;
    border-bottom: 1px solid var(--line-soft);
    font-family: var(--mono);
    font-size: 7.5px;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--muted-2);
}
.who-row {
    display: grid;
    grid-template-columns: 1.05fr 2fr .85fr .85fr .4fr;
    gap: .8rem;
    align-items: center;
    padding: .58rem 0;
    border-bottom: 1px solid var(--line-soft);
}
.who-row:last-of-type { border-bottom: 0; }
.who-name { font-size: .8rem; font-weight: 600; color: var(--cream); display: flex; flex-direction: column; }
.who-name span { font-family: var(--mono); font-size: 7px; font-weight: 400; color: var(--muted-2); margin-top: .1rem; }
.who-track { position: relative; height: 5px; background: rgba(255, 255, 255, .06); border-radius: 999px; }
.who-fill { display: block; height: 5px; border-radius: 999px; }
.who-marker { position: absolute; left: 25%; top: -2px; width: 1px; height: 9px; background: rgba(244, 237, 224, .38); }
.who-reading { font-family: var(--mono); font-size: .72rem; color: var(--cream); text-align: right; }
.who-reading span { font-size: .6rem; color: var(--muted-2); }
.who-guide { font-family: var(--mono); font-size: .66rem; color: var(--muted); text-align: right; }
.who-ratio { font-family: var(--mono); font-size: .7rem; text-align: right; }

/* ---------------------------------------------------------------- windows */

.window-card {
    height: 100%;
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1rem 1.05rem .95rem 1.05rem;
    background:
        radial-gradient(110% 110% at 0% 0%, rgba(255, 255, 255, .05), transparent 55%),
        linear-gradient(150deg, rgba(18, 32, 46, .8), rgba(8, 15, 24, .64));
    border-bottom: 2px solid var(--accent);
    transition: transform .2s ease, border-color .2s ease;
}
.window-card:hover { transform: translateY(-2px); }
.window-top { display: flex; justify-content: space-between; align-items: center; gap: .5rem; }
.window-index { font-family: var(--display); font-size: 1.15rem; color: var(--accent); }
.window-tag { font-family: var(--mono); font-size: 6.8px; letter-spacing: .13em; color: var(--muted-2); }
.window-time { font-family: var(--mono); font-size: .72rem; color: var(--cream); margin-top: .5rem; letter-spacing: .02em; }
.window-aqi { font-family: var(--display); font-size: 2rem; line-height: 1; margin-top: .3rem; letter-spacing: -.04em; }
.window-aqi span { font-family: var(--mono); font-size: 7.5px; color: var(--muted-2); letter-spacing: .06em; }
.window-cat { font-family: var(--mono); font-size: 7px; color: var(--muted); margin-top: .35rem; letter-spacing: .03em; }

.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .65rem; height: 100%; }
.stat-card {
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: .85rem .9rem;
    background: linear-gradient(150deg, rgba(18, 32, 46, .7), rgba(8, 15, 24, .55));
    border-top: 1px solid rgba(255, 255, 255, .07);
    height: 100%;
}
.stat-label { font-family: var(--mono); font-size: 7.5px; letter-spacing: .13em; color: var(--muted-2); text-transform: uppercase; }
.stat-value { font-family: var(--display); font-size: 1.65rem; letter-spacing: -.035em; color: var(--cream); margin-top: .25rem; line-height: 1; }
.stat-sub { font-family: var(--mono); font-size: 7px; color: var(--muted); margin-top: .35rem; line-height: 1.5; }

/* ---------------------------------------------------------------- heatmap */

.heat-card { overflow: hidden; }
.heat-grid { margin-top: 1rem; display: flex; flex-direction: column; gap: 3px; width: 100%; }
.heat-head, .heat-row { display: grid; grid-template-columns: 40px repeat(24, minmax(4px, 1fr)); gap: 3px; align-items: center; }

.history-layout {
    display: grid;
    grid-template-columns: minmax(0, 1.65fr) minmax(0, 1fr);
    gap: 1.1rem;
    align-items: stretch;
}
.history-layout .glass-card { height: 100%; }
.history-layout .stats-grid { align-content: stretch; }

.about-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
}
.about-grid .about-card { height: 100%; }
.heat-head span { font-family: var(--mono); font-size: 6.5px; color: var(--muted-2); text-align: center; }
.heat-day { font-family: var(--mono); font-size: 7.5px; color: var(--muted); letter-spacing: .04em; }
.heat-cell { display: block; aspect-ratio: 1 / 1; border-radius: 2.5px; opacity: .88; transition: transform .12s ease, opacity .12s ease; }
.heat-cell:hover { transform: scale(1.35); opacity: 1; position: relative; z-index: 2; }
.heat-cell.empty { background: rgba(255, 255, 255, .035); }
.heat-legend { display: flex; flex-wrap: wrap; gap: .7rem; margin-top: 1rem; padding-top: .8rem; border-top: 1px solid var(--line-soft); }
.legend-item { display: inline-flex; align-items: center; gap: .3rem; font-family: var(--mono); font-size: 6.8px; letter-spacing: .04em; color: var(--muted); }
.legend-dot { width: 5px; height: 5px; border-radius: 50%; }

/* --------------------------------------------------------------- exposure */

.exposure-metric {
    height: 100%;
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1rem 1.1rem;
    background:
        radial-gradient(110% 100% at 0% 0%, rgba(255, 255, 255, .04), transparent 60%),
        linear-gradient(150deg, rgba(18, 32, 46, .8), rgba(8, 15, 24, .6));
    border-top: 2px solid var(--accent);
}
.exposure-value { font-family: var(--display); font-size: 2.5rem; letter-spacing: -.045em; line-height: 1; margin-top: .4rem; }
.exposure-value span { font-family: var(--mono); font-size: 8px; color: var(--muted-2); margin-left: .35rem; letter-spacing: .06em; }

.index-card { border-top: 2px solid var(--accent); }
.index-value { font-family: var(--display); font-size: 3.6rem; letter-spacing: -.05em; line-height: 1; margin-top: .8rem; color: var(--accent); }
.index-value span { font-family: var(--mono); font-size: 10px; color: var(--muted-2); letter-spacing: .04em; }
.index-track { height: 7px; border-radius: 999px; background: rgba(255, 255, 255, .07); overflow: hidden; margin-top: .9rem; }
.index-track span { display: block; height: 100%; border-radius: 999px; }
.index-summary { margin-top: .9rem; font-size: .86rem; line-height: 1.7; color: #C6D0DA; }
.index-interpretation { font-size: .8rem; line-height: 1.72; color: var(--muted); }
.lever-list { display: flex; flex-direction: column; gap: .45rem; font-size: .8rem; line-height: 1.6; color: var(--muted); }
.lever-list span { display: block; }

/* --------------------------------------------------------------- pathways */

.pathway-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; }
.pathway-card {
    display: flex;
    gap: .85rem;
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1rem 1.05rem;
    background: rgba(255, 255, 255, .025);
    transition: border-color .2s ease, background .2s ease, transform .2s ease;
}
.pathway-card:hover { border-color: rgba(111, 227, 214, .28); background: rgba(111, 227, 214, .035); transform: translateY(-2px); }
.pathway-number { font-family: var(--mono); font-size: 9px; color: var(--coral); letter-spacing: .08em; padding-top: .15rem; }
.pathway-card h4 { margin: 0 0 .25rem 0; font-size: .84rem; }
.pathway-card p { margin: 0; font-size: .76rem; line-height: 1.62; color: var(--muted); }

.chem-equation {
    border: 1px solid rgba(111, 227, 214, .22);
    border-radius: 18px;
    padding: 1.4rem;
    text-align: center;
    font-family: var(--mono);
    font-size: 1.02rem;
    line-height: 2;
    color: var(--cyan);
    background: radial-gradient(100% 100% at 50% 0%, rgba(111, 227, 214, .07), rgba(255, 255, 255, .012));
}
.chem-equation small { display: block; margin-top: .55rem; font-family: var(--body); font-size: .72rem; line-height: 1.6; color: var(--muted); }

/* ---------------------------------------------------------- alert / demo */

.alert-banner {
    display: flex;
    align-items: center;
    gap: 1rem;
    border: 1px solid rgba(var(--accent-rgb), .35);
    border-radius: 18px;
    padding: .95rem 1.1rem;
    margin: .5rem 0 1rem 0;
    background:
        radial-gradient(105% 160% at 0% 0%, rgba(var(--accent-rgb), .14), transparent 60%),
        rgba(255, 255, 255, .025);
}
.alert-icon {
    flex: 0 0 auto;
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    display: grid;
    place-items: center;
    border: 1px solid rgba(var(--accent-rgb), .45);
    color: var(--accent);
    font-family: var(--display);
    font-size: 1.15rem;
}
.alert-body { flex: 1; }
.alert-body strong { font-size: .88rem; }
.alert-body p { margin: .15rem 0 0 0; font-size: .78rem; line-height: 1.6; color: var(--muted); }
.alert-body b { color: var(--accent); }
.alert-tag { font-family: var(--mono); font-size: 7.5px; letter-spacing: .13em; color: var(--accent); border: 1px solid rgba(var(--accent-rgb), .35); border-radius: 999px; padding: .3rem .55rem; white-space: nowrap; }

.demo-banner {
    display: flex;
    gap: .9rem;
    align-items: flex-start;
    border: 1px solid rgba(233, 187, 120, .35);
    border-radius: 18px;
    padding: .9rem 1.05rem;
    margin: .5rem 0 1rem 0;
    background: rgba(233, 187, 120, .055);
}
.demo-badge { flex: 0 0 auto; font-family: var(--mono); font-size: 7.5px; letter-spacing: .13em; color: var(--amber); border: 1px solid rgba(233, 187, 120, .4); border-radius: 999px; padding: .3rem .5rem; }
.demo-banner strong { font-size: .84rem; color: var(--cream); }
.demo-banner p { margin: .2rem 0 0 0; font-size: .76rem; line-height: 1.62; color: var(--muted); }
.demo-reason { display: block; margin-top: .25rem; font-family: var(--mono); font-size: 7.5px; color: var(--muted-2); word-break: break-word; }

/* ---------------------------------------------------------------- sidebar */

.brand-block { padding: .2rem 0 1.35rem 0; }
.brand-row { display: flex; align-items: center; gap: .65rem; }
.brand-mark { width: 2rem; height: 2rem; color: var(--cyan); display: inline-flex; }
.brand-mark svg { width: 100%; height: 100%; }
.brand-mark img { width: 100%; height: 100%; display: block; }
.brand-word { font-family: var(--body); font-size: 1.45rem; font-weight: 700; letter-spacing: .16em; color: var(--cream); line-height: 1; }
.brand-word span { color: var(--coral); }
.brand-word.small { font-size: 1.02rem; letter-spacing: .13em; }
.brand-tag { margin-top: .35rem; font-family: var(--mono); font-size: 7.5px; letter-spacing: .14em; text-transform: uppercase; color: var(--muted-2); }

.side-label {
    display: flex;
    align-items: center;
    gap: .5rem;
    font-family: var(--mono);
    font-size: 8px;
    letter-spacing: .16em;
    color: var(--cyan);
    text-transform: uppercase;
    margin: .2rem 0 .6rem 0;
}
.side-label::before { content: ""; width: 16px; height: 1px; background: var(--cyan); opacity: .55; }
.side-title { font-family: var(--body); font-weight: 600; font-size: 1rem; margin: 0 0 .55rem 0; }
.side-copy { font-size: .76rem; line-height: 1.6; color: var(--muted); }
.side-note { font-family: var(--mono); font-size: 7.5px; line-height: 1.8; letter-spacing: .04em; color: var(--muted-2); }
.side-note b { color: var(--muted); font-weight: 500; }

.side-aqi {
    position: relative;
    border: 1px solid rgba(var(--accent-rgb), .28);
    border-radius: 18px;
    padding: .9rem .95rem;
    margin: .2rem 0 1rem 0;
    background:
        radial-gradient(110% 130% at 0% 0%, rgba(var(--accent-rgb), .14), transparent 65%),
        rgba(255, 255, 255, .025);
}
.side-aqi-top { display: flex; justify-content: space-between; align-items: center; font-family: var(--mono); font-size: 7.5px; letter-spacing: .13em; color: var(--accent); }
.side-aqi-value { font-family: var(--display); font-size: 2.4rem; line-height: 1; letter-spacing: -.04em; color: var(--accent); margin-top: .35rem; }
.side-aqi-cat { font-family: var(--mono); font-size: 8px; letter-spacing: .1em; text-transform: uppercase; color: var(--cream); opacity: .76; margin-top: .2rem; }
.side-aqi-track { height: 3px; border-radius: 999px; background: rgba(255, 255, 255, .08); margin-top: .65rem; overflow: hidden; }
.side-aqi-track span { display: block; height: 100%; border-radius: 999px; }
.side-aqi-copy { font-size: .7rem; line-height: 1.55; color: var(--muted); margin-top: .55rem; }

/* ----------------------------------------------------------------- footer */

.site-footer {
    display: grid;
    grid-template-columns: 1.5fr 1fr 1fr 1.3fr;
    gap: 2rem;
    border-top: 1px solid var(--line);
    margin-top: 3.2rem;
    padding: 2rem 0 1.4rem 0;
}
.footer-brand p { margin-top: .7rem; max-width: 20rem; font-size: .76rem; line-height: 1.7; color: var(--muted); }
.footer-col { display: flex; flex-direction: column; gap: .42rem; font-size: .74rem; color: var(--muted); }
.footer-label { font-family: var(--mono); font-size: 7.5px; letter-spacing: .16em; color: var(--muted-2); margin-bottom: .25rem; }
.footer-note p { margin-top: .35rem; font-size: .72rem; line-height: 1.65; color: var(--muted); }
.footer-rule {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
    border-top: 1px solid var(--line-soft);
    padding: .9rem 0 1.5rem 0;
    font-family: var(--mono);
    font-size: 7px;
    letter-spacing: .14em;
    color: var(--muted-2);
}

/* --------------------------------------------------------------- utilities */

.muted { color: var(--muted) !important; }
.coral { color: var(--coral) !important; }
.cyan { color: var(--cyan) !important; }
.amber { color: var(--amber) !important; }
.center { text-align: center; }
.mt-0 { margin-top: 0 !important; }
.mt-1 { margin-top: .6rem !important; }
.mt-2 { margin-top: 1.2rem !important; }
.mb-1 { margin-bottom: .6rem !important; }

/* ---------------------------------------------------------------- mobile */

@media (max-width: 1100px) {
    [data-testid="stMainBlockContainer"] { padding: 1.2rem 1.45rem 2.8rem 1.45rem; }
    .hero-grid { grid-template-columns: 1fr; }
    .gauge-card { max-width: 440px; width: 100%; margin: 0 auto; }
    .site-footer { grid-template-columns: 1.4fr 1fr 1fr; }
    .footer-note { grid-column: 1 / -1; }
    .history-layout { grid-template-columns: 1fr; }
    .about-grid { grid-template-columns: 1fr; }
    .topbar-sub, .topbar-slash { display: none; }
    .stTabs [data-baseweb="tab-list"] {
        width: 100%;
        flex-wrap: wrap;
        overflow: visible;
        border-radius: 22px;
        row-gap: .2rem;
    }
}

@media (max-width: 820px) {
    [data-testid="stMainBlockContainer"] { padding: 1rem 1.1rem 2.4rem 1.1rem; }
    .hero-title { font-size: clamp(3rem, 12vw, 5rem); }
    .hero-coord { font-size: 8px; }
    .who-head { display: none; }
    .who-row { grid-template-columns: 1fr auto; gap: .35rem .7rem; padding: .7rem 0; }
    .who-name { grid-column: 1; }
    .who-ratio { grid-column: 2; grid-row: 1; }
    .who-track { grid-column: 1 / -1; }
    .who-reading { grid-column: 1; text-align: left; }
    .who-guide { grid-column: 2; }
    .pathway-grid { grid-template-columns: 1fr; }
    .site-footer { grid-template-columns: 1fr 1fr; gap: 1.4rem; }
    .stTabs [data-baseweb="tab"] { padding: .42rem .7rem; font-size: 8.5px; }
    .stTabs [data-baseweb="tab"] p { font-size: 8.5px !important; }
}

@media (max-width: 560px) {
    .hero-grid { padding-top: 1.6rem; }
    .hero-title { font-size: 3.15rem; }
    .hero-meta { gap: .4rem; }
    .hero-chip { font-size: 8px; padding: .32rem .55rem; }
    .gauge-card { padding: .95rem .95rem 1rem .95rem; }
    .gauge-readout { padding-top: 1rem; }
    .gauge-number { font-size: 3.1rem; }
    .gauge-foot { flex-direction: column; align-items: flex-start; }
    .stats-grid { grid-template-columns: 1fr; }
    .site-footer { grid-template-columns: 1fr; }
    .alert-banner { flex-wrap: wrap; }
    .alert-tag { display: none; }
    .demo-banner { flex-direction: column; }
    .topbar-place { font-size: 8px; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: .001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: .001ms !important;
    }
}
"""
