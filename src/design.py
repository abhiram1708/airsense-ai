"""AirSense visual system — quiet white pages, green ink, editorial type."""

SITE_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,300..700&family=Instrument+Sans:ital,wght@0,400..700;1,400..600&display=swap');

:root {
    --paper: #ffffff;
    --tint: #f6faf7;
    --tint-2: #eef6f1;
    --ink: #101f18;
    --ink-soft: #33473c;
    --muted: #64796c;
    --muted-2: #8b9c92;
    --green: #1f7a4f;
    --green-deep: #145737;
    --green-soft: rgba(31, 122, 79, .09);
    --line: #e2ede7;
    --line-soft: #edf4f0;
    --amber: #a87c25;
    --display: 'Fraunces', Georgia, 'Times New Roman', serif;
    --body: 'Instrument Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --mono: ui-monospace, SFMono-Regular, Menlo, monospace;
    --radius: 22px;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
    background: var(--paper) !important;
    color: var(--ink) !important;
    font-family: var(--body) !important;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(60% 40% at 80% -10%, rgba(31, 122, 79, .07), transparent 65%),
        radial-gradient(45% 35% at -5% 22%, rgba(31, 122, 79, .05), transparent 70%),
        #ffffff !important;
}

[data-testid="stHeader"] { background: transparent !important; backdrop-filter: none !important; }
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stAppDeployButton"], [data-testid="stToolbar"] { display: none !important; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }

[data-testid="stMain"] { background: transparent !important; }
[data-testid="stMainBlockContainer"] {
    max-width: 1120px;
    padding: 1.6rem 2rem 4.5rem 2rem;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { line-height: 1.68; color: var(--ink-soft); }
[data-testid="stMarkdownContainer"] { font-family: var(--body); }
[data-testid="stMarkdownContainer"] p { font-size: .96rem; }
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 { font-family: var(--display); font-weight: 400; letter-spacing: -.02em; }

/* ------------------------------------------------------------------ shell */

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding-bottom: 1.1rem;
    border-bottom: 1px solid var(--line-soft);
}
.brand { display: flex; align-items: center; gap: .6rem; }
.brand svg { display: block; }
.brand-name {
    font-family: var(--display);
    font-size: 1.12rem;
    letter-spacing: -.02em;
    color: var(--ink);
}
.brand-name em { font-style: italic; color: var(--green); }
.topbar-meta { display: flex; align-items: center; gap: .9rem; }
.topbar-place { font-size: .82rem; color: var(--muted); }
.topbar-place b { color: var(--ink); font-weight: 500; }
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: .42rem;
    padding: .3rem .66rem;
    border-radius: 999px;
    border: 1px solid rgba(31, 122, 79, .22);
    background: var(--green-soft);
    color: var(--green-deep);
    font-size: .72rem;
    letter-spacing: .01em;
}
.status-pill::before {
    content: "";
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 0 3px rgba(31, 122, 79, .16);
}
.status-pill.demo { border-color: rgba(168, 124, 37, .28); background: rgba(168, 124, 37, .09); color: #7d5b14; }
.status-pill.demo::before { background: var(--amber); box-shadow: 0 0 0 3px rgba(168, 124, 37, .16); }

/* ------------------------------------------------------------------- hero */

.hero-copy { padding: 2.9rem 0 2.2rem 0; }
.eyebrow {
    display: inline-flex;
    align-items: center;
    gap: .55rem;
    font-size: .74rem;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: var(--green);
    font-weight: 500;
}
.eyebrow::before { content: ""; width: 26px; height: 1px; background: currentColor; opacity: .5; }
.hero-copy h1 {
    margin: .9rem 0 0 0;
    font-family: var(--display);
    font-weight: 350;
    font-size: clamp(2.7rem, 5.4vw, 4.35rem);
    line-height: 1.02;
    letter-spacing: -.035em;
    color: var(--ink);
}
.hero-copy h1 em { font-style: italic; color: var(--green); }
.hero-copy .hero-lede {
    margin: 1.1rem 0 0 0;
    max-width: 34rem;
    font-size: 1rem;
    line-height: 1.66;
    color: var(--muted);
}
.hero-lede b { color: var(--ink); font-weight: 500; }

.st-key-search_box {
    margin-top: 3.3rem;
    padding: 1.2rem 1.25rem 1.1rem 1.25rem;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: linear-gradient(160deg, #ffffff, var(--tint));
    box-shadow: 0 18px 50px rgba(16, 54, 36, .06);
}
.st-key-search_box .stTextInput { margin-top: .1rem; }
.st-key-search_box .stButton { margin-top: .45rem; }
.st-key-search_box [data-testid="stForm"] { border: 0 !important; padding: 0 !important; background: transparent !important; box-shadow: none !important; }
.st-key-search_box [data-testid="stFormSubmitButton"] { margin-top: .45rem; }
.search-label {
    font-family: var(--body);
    font-size: .7rem;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--muted-2);
    margin-bottom: .55rem;
}
.search-hint { font-size: .76rem; line-height: 1.6; color: var(--muted-2); margin-top: .6rem; }

/* ---------------------------------------------------------------- readout */

.now-wrap { padding-bottom: 1.4rem; }
.now-card {
    display: grid;
    grid-template-columns: minmax(190px, .62fr) minmax(0, 1.38fr);
    gap: 1.8rem;
    align-items: center;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: linear-gradient(150deg, #ffffff, var(--tint));
    padding: 1.5rem 1.7rem;
}
.now-aqi { display: flex; flex-direction: column; gap: .15rem; }
.now-kicker { font-size: .68rem; letter-spacing: .13em; text-transform: uppercase; color: var(--muted-2); }
.now-value {
    display: flex;
    align-items: baseline;
    gap: .5rem;
    font-family: var(--display);
    font-size: 3.4rem;
    line-height: 1;
    letter-spacing: -.04em;
    color: var(--ink);
}
.now-value small { font-family: var(--body); font-size: .72rem; letter-spacing: .1em; text-transform: uppercase; color: var(--muted-2); }
.now-band { font-size: .88rem; color: var(--ink-soft); }
.now-band b { color: var(--band, var(--green)); font-weight: 600; }
.now-source { font-size: .72rem; color: var(--muted-2); margin-top: .35rem; }
.pol-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1rem 1.4rem; }
.pol { display: flex; flex-direction: column; gap: .32rem; }
.pol-top { display: flex; align-items: baseline; justify-content: space-between; gap: .4rem; }
.pol-name { font-size: .76rem; color: var(--muted); }
.pol-val { font-size: .92rem; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums; }
.pol-val span { font-size: .66rem; font-weight: 400; color: var(--muted-2); margin-left: .15rem; }
.pol-track { height: 4px; border-radius: 999px; background: var(--line-soft); overflow: hidden; }
.pol-track i { display: block; height: 100%; border-radius: 999px; background: var(--bar, var(--green)); }

/* --------------------------------------------------------------- sections */

.section { padding-top: 2.6rem; }
.section-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 2rem; flex-wrap: wrap; }
.section-kicker { font-size: .72rem; letter-spacing: .13em; text-transform: uppercase; color: var(--green); }
.section-title {
    margin: .45rem 0 0 0;
    font-family: var(--display);
    font-weight: 350;
    font-size: clamp(1.65rem, 3vw, 2.2rem);
    letter-spacing: -.03em;
    color: var(--ink);
}
.section-note { max-width: 27rem; font-size: .88rem; line-height: 1.6; color: var(--muted); }
.section-body { margin-top: 1.35rem; }

/* -------------------------------------------------------------- controls */

.stButton > button, .stFormSubmitButton > button {
    border-radius: 999px;
    border: 1px solid var(--line);
    background: #ffffff;
    color: var(--ink);
    font-family: var(--body);
    font-size: .86rem;
    font-weight: 500;
    padding: .5rem 1rem;
    box-shadow: none;
    transition: background .16s ease, border-color .16s ease, color .16s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    border-color: rgba(31, 122, 79, .35);
    color: var(--green-deep);
    background: var(--green-soft);
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"],
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"],
.stFormSubmitButton > button[kind="primaryFormSubmit"] {
    background: var(--green) !important;
    border-color: var(--green) !important;
    color: #ffffff !important;
}
.stButton > button[kind="primary"] p, .stFormSubmitButton > button[kind="primary"] p,
[data-testid="stBaseButton-primary"] p,
[data-testid="stBaseButton-primary"] div,
[data-testid="stBaseButton-primary"] span,
[data-testid="stBaseButton-primaryFormSubmit"] p,
[data-testid="stBaseButton-primaryFormSubmit"] div,
[data-testid="stBaseButton-primaryFormSubmit"] span,
.stFormSubmitButton > button[kind="primaryFormSubmit"] p {
    color: #ffffff !important;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover {
    background: var(--green-deep) !important;
    border-color: var(--green-deep) !important;
    color: #ffffff !important;
}
.stTextInput input {
    border-radius: 12px !important;
    border: 1px solid var(--line) !important;
    background: #ffffff !important;
    color: var(--ink) !important;
    font-family: var(--body) !important;
    font-size: .9rem !important;
    padding: .55rem .8rem !important;
}
.stTextInput input::placeholder { color: var(--muted-2) !important; }
.stTextInput input:focus { border-color: rgba(31, 122, 79, .45) !important; box-shadow: 0 0 0 3px rgba(31, 122, 79, .1) !important; }
.stTextInput label, .stSelectbox label { font-family: var(--body) !important; font-size: .72rem !important; color: var(--muted) !important; }
.stSelectbox [data-baseweb="select"] > div {
    border-radius: 12px !important;
    border-color: var(--line) !important;
    background: #ffffff !important;
    font-size: .84rem;
}

[data-testid="stPills"] button, [data-testid="stButtonGroup"] button {
    border-radius: 999px !important;
    border: 1px solid var(--line) !important;
    background: #ffffff !important;
    color: var(--muted) !important;
    font-family: var(--body) !important;
    font-size: .78rem !important;
    padding: .28rem .7rem !important;
    min-height: 0 !important;
}
[data-testid="stPills"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[aria-checked="true"] {
    background: var(--green-soft) !important;
    border-color: rgba(31, 122, 79, .3) !important;
    color: var(--green-deep) !important;
}

/* -------------------------------------------------------------- chat fab */

.st-key-chat_fab {
    position: fixed;
    right: 24px;
    bottom: 24px;
    z-index: 1000;
    width: auto;
}
.st-key-chat_fab button {
    width: 58px;
    height: 58px;
    padding: 0;
    border-radius: 50%;
    border: 0;
    font-size: 1.35rem;
    line-height: 1;
    color: #ffffff;
    background: linear-gradient(150deg, #2b9263, var(--green-deep));
    box-shadow: 0 14px 34px rgba(20, 87, 55, .32);
}
.st-key-chat_fab button:hover {
    background: linear-gradient(150deg, #34a773, var(--green));
    color: #ffffff;
    transform: translateY(-2px);
}

/* ------------------------------------------------------------ chat panel */

.st-key-chat_panel {
    position: fixed;
    right: 24px;
    bottom: 96px;
    z-index: 1001;
    width: min(394px, calc(100vw - 32px));
    height: auto;
    max-height: min(596px, calc(100vh - 140px));
    overflow-y: auto;
    gap: .42rem !important;
    padding: 1.05rem 1.05rem .9rem 1.05rem;
    border: 1px solid var(--line);
    border-radius: 24px;
    background: rgba(255, 255, 255, .98);
    backdrop-filter: blur(14px);
    box-shadow: 0 34px 80px rgba(12, 44, 29, .2);
    overflow: hidden;
}
.chat-head { display: flex; align-items: center; justify-content: space-between; gap: .8rem; padding-right: 2.2rem; }
.st-key-chat_close {
    position: absolute !important;
    top: 14px;
    right: 14px;
    width: 30px;
    z-index: 3;
}
.chat-title { font-family: var(--display); font-size: 1.12rem; letter-spacing: -.02em; color: var(--ink); }
.chat-title span { color: var(--green); font-style: italic; }
.chat-sub { font-size: .72rem; color: var(--muted-2); margin-top: .12rem; }
.chat-rule { height: 1px; background: var(--line-soft); margin: .7rem 0 .6rem 0; }
.chat-suggest { display: flex; flex-wrap: wrap; gap: .32rem; padding-bottom: .55rem; }
.st-key-chat_thread [data-testid="stLayoutWrapper"],
.st-key-chat_thread [data-testid="stVerticalBlock"] {
    height: auto !important;
    max-height: 250px;
}
.st-key-chat_panel [data-testid="stPills"] { margin: 0; }
.st-key-chat_panel [data-testid="stPills"] button {
    font-size: .71rem !important;
    padding: .22rem .58rem !important;
    min-height: 0 !important;
    height: auto !important;
    border-radius: 999px !important;
    background: var(--tint) !important;
    border: 1px solid var(--line) !important;
    color: var(--muted) !important;
}
.st-key-chat_panel [data-testid="stPills"] button[aria-checked="true"] {
    background: var(--green-soft) !important;
    border-color: rgba(31, 122, 79, .28) !important;
    color: var(--green-deep) !important;
}
.st-key-chat_suggest button {
    font-size: .7rem !important;
    line-height: 1.3 !important;
    padding: .3rem .4rem !important;
    min-height: 0 !important;
    height: auto !important;
    border-radius: 12px !important;
    background: var(--tint) !important;
    border: 1px solid var(--line) !important;
    color: var(--muted) !important;
    white-space: normal !important;
}
.st-key-chat_suggest button:hover { color: var(--green-deep) !important; border-color: rgba(31,122,79,.3) !important; background: var(--green-soft) !important; }
.st-key-chat_close button {
    width: 30px !important;
    height: 30px !important;
    min-height: 30px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    font-size: .82rem !important;
    color: var(--muted) !important;
    background: var(--tint) !important;
    border: 1px solid var(--line) !important;
    margin-left: auto;
}

[data-testid="stChatMessage"] {
    background: transparent !important;
    padding: .1rem 0 !important;
}
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"],
[data-testid="stChatMessageAvatar"] { display: none !important; }
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
    background: var(--tint);
    border: 1px solid var(--line-soft);
    border-radius: 16px;
    padding: .6rem .75rem;
    font-size: .84rem;
    line-height: 1.6;
    color: var(--ink-soft);
}
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p { font-size: .84rem !important; margin: 0 0 .4rem 0; line-height: 1.62; }
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p:last-child { margin-bottom: 0; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"],
[data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageContent"] {
    background: var(--green-soft);
    border-color: rgba(31, 122, 79, .16);
    color: var(--green-deep);
}
.st-key-chat_panel [data-testid="stForm"] {
    border: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}
.st-key-chat_panel [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: .4rem !important;
    align-items: center;
}
.st-key-chat_panel [data-testid="stForm"] [data-testid="stColumn"] { min-width: 0; }
.st-key-chat_panel [data-testid="stForm"] [data-testid="stColumn"]:last-child { flex: 0 0 46px; }
.chat-form .stTextInput input { border-radius: 999px !important; font-size: .84rem !important; height: 40px !important; min-height: 40px !important; }
.chat-form [data-testid="stForm"] { margin: 0; }
.st-key-chat_panel .stTextInput { margin-bottom: 0; }
.chat-form .stFormSubmitButton button { border-radius: 999px; min-width: 44px; padding: .45rem .8rem; }
.chat-foot { font-size: .64rem; line-height: 1.45; color: var(--muted-2); padding-top: .1rem; }
@media (max-height: 780px) { .chat-foot { display: none; } }

/* ---------------------------------------------------------------- footer */

.site-footer {
    margin-top: 3.6rem;
    padding-top: 1.4rem;
    border-top: 1px solid var(--line-soft);
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1.5rem;
    flex-wrap: wrap;
    font-size: .74rem;
    line-height: 1.65;
    color: var(--muted-2);
}
.site-footer b { color: var(--muted); font-weight: 500; }

/* ---------------------------------------------------------------- mobile */

@media (max-width: 900px) {
    .hero-copy { padding: 1.9rem 0 .4rem 0; }
    .st-key-search_box { margin-top: .6rem; max-width: 480px; }
    .now-card { grid-template-columns: 1fr; gap: 1.2rem; padding: 1.3rem 1.25rem; }
    .pol-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .9rem 1.2rem; }
    .topbar-place { display: none; }
}

@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] { padding: 1rem .9rem 5.5rem .9rem; }
    .hero-copy h1 { font-size: clamp(2.4rem, 11vw, 3.1rem); }
    .hero-copy .hero-lede { font-size: .93rem; }
    .topbar { padding-bottom: .85rem; }
    .status-pill { font-size: .66rem; padding: .26rem .55rem; }
    .now-value { font-size: 2.9rem; }
    .section { padding-top: 2rem; }
    .section-head { gap: .6rem; }
    .section-note { font-size: .84rem; }
    .st-key-chat_panel {
        right: 10px;
        left: 10px;
        bottom: 88px;
        width: auto;
        height: auto;
        max-height: calc(100vh - 128px);
        border-radius: 20px;
        padding: .95rem .85rem .85rem .85rem;
    }
    .st-key-chat_fab { right: 16px; bottom: 16px; }
    .st-key-chat_fab button { width: 54px; height: 54px; font-size: 1.25rem; }
    .site-footer { margin-top: 2.4rem; gap: .6rem; }
}

@media (hover: none) {
    .stButton > button:hover, .st-key-chat_fab button:hover { transform: none; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration: .001ms !important; transition-duration: .001ms !important; }
}
"""
