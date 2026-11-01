"""
PrepPulse AI - UI layer
-----------------------
Design idea: an interview is a *live signal*. The interviewer speaks (waveform),
a spotlight sits on the question, and your score fills like a pulse ring.

Palette
  ink    #0A0B14   page
  panel  #12142A   surfaces
  violet #7C5CFF   brand / actions
  amber  #FFB547   spotlight / warnings
  mint   #4ADE9C   strong results
  coral  #FF6B7A   gaps / weak results
"""
import html as _html
import inspect

import streamlit as st


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def _h(s: str) -> str:
    """Collapse HTML to one line. Indented HTML would be parsed as a markdown code block."""
    return "".join(line.strip() for line in s.strip().splitlines())


def _esc(x) -> str:
    return _html.escape(str(x if x is not None else ""))


def stretch(fn) -> dict:
    """Full-width kwargs that work on old and new Streamlit (use_container_width was replaced by width='stretch')."""
    try:
        if "width" in inspect.signature(fn).parameters:
            return {"width": "stretch"}
    except (TypeError, ValueError):
        pass
    return {"use_container_width": True}


def _clamp_score(score) -> int:
    try:
        return max(0, min(100, int(round(float(score)))))
    except (TypeError, ValueError):
        return 0


# ----------------------------------------------------------------------------
# global CSS
# ----------------------------------------------------------------------------
def apply_custom_css():
    """Injects the PrepPulse design system into Streamlit."""
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Figtree:wght@400;500;600&display=swap');

    :root{
        --ink:#0A0B14; --panel:#12142A; --panel-2:#181B38; --line:#262A4D;
        --violet:#7C5CFF; --violet-soft:#A18BFF; --amber:#FFB547;
        --mint:#4ADE9C; --coral:#FF6B7A;
        --text:#ECEBFF; --mute:#9A9CC4;
        --display:'Bricolage Grotesque','Figtree',system-ui,sans-serif;
        --body:'Figtree',system-ui,-apple-system,sans-serif;
    }

    /* registered props let CSS animate the ring fill and the number inside it */
    @property --v { syntax:'<integer>'; inherits:true; initial-value:0; }

    /* ---------- page ---------- */
    .stApp{
        background:
            radial-gradient(700px 480px at 12% 8%,  rgba(124,92,255,.14), transparent 62%),
            radial-gradient(600px 440px at 92% 88%, rgba(255,181,71,.07), transparent 62%),
            var(--ink);
        background-repeat:no-repeat;
        isolation:isolate;
        color:var(--text);
    }
    .stApp::before{ content:""; position:fixed; inset:-15%; z-index:-1; pointer-events:none; will-change:transform;
        background:
            radial-gradient(520px 380px at 25% 20%, rgba(124,92,255,.16), transparent 65%),
            radial-gradient(460px 340px at 80% 80%, rgba(255,181,71,.09), transparent 65%);
        animation:drift 28s ease-in-out infinite alternate; }
    @keyframes drift{ from{transform:translate3d(-3%,-2%,0)} to{transform:translate3d(4%,3%,0)} }

    .stApp p,.stApp label,.stApp li,.stApp textarea,.stApp button,
    [data-testid="stMarkdownContainer"]{ font-family:var(--body); }
    [data-testid="stHeader"]{ background:transparent; }
    footer{ visibility:hidden; }
    .block-container{ padding-top:2.2rem; max-width:1200px; }
    ::-webkit-scrollbar{ width:8px; height:8px }
    ::-webkit-scrollbar-thumb{ background:var(--line); border-radius:8px }

    /* ---------- sidebar ---------- */
    [data-testid="stSidebar"]{
        background:linear-gradient(180deg,#0F1128 0%,#0A0B14 100%);
        border-right:1px solid var(--line);
    }
    .brand{ display:flex; align-items:center; gap:12px; margin:4px 0 2px; }
    .brand-mark{ display:flex; align-items:center; gap:3px; height:34px; padding:0 10px;
        border-radius:12px; background:rgba(124,92,255,.14); border:1px solid rgba(124,92,255,.4); }
    .brand-mark i{ display:block; width:3px; height:100%; max-height:18px; border-radius:3px;
        background:linear-gradient(var(--violet-soft),var(--amber)); transform-origin:center;
        animation:eq 1.1s ease-in-out infinite; }
    .brand-mark i:nth-child(2){ animation-delay:.15s } .brand-mark i:nth-child(3){ animation-delay:.3s }
    .brand-mark i:nth-child(4){ animation-delay:.45s } .brand-mark i:nth-child(5){ animation-delay:.6s }
    .brand-title{ font-family:var(--display); font-weight:800; font-size:1.45rem; letter-spacing:-.02em;
        color:var(--text); margin:0; line-height:1; }
    .brand-sub{ color:var(--mute); font-size:.82rem; margin:6px 0 4px; }

    [data-testid="stSidebar"] [data-testid="stRadio"] > label{ display:none; }
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"]{ gap:6px; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label{
        width:100%; padding:.7rem .95rem; border-radius:14px; border:1px solid transparent;
        transition:background .2s, border-color .2s, transform .2s; cursor:pointer; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child{ display:none; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover{ background:rgba(124,92,255,.10); transform:translateX(3px); }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){
        background:linear-gradient(90deg,rgba(124,92,255,.26),rgba(124,92,255,.04));
        border-color:rgba(124,92,255,.5); }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p{ color:#fff; font-weight:600; }

    .status-pill{ display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:999px;
        background:rgba(74,222,156,.08); border:1px solid rgba(74,222,156,.3); color:var(--mint);
        font-size:.8rem; font-weight:600; }
    .status-pill b{ width:8px; height:8px; border-radius:50%; background:var(--mint); position:relative; }
    .status-pill b::after{ content:""; position:absolute; inset:-4px; border-radius:50%;
        border:2px solid var(--mint); animation:ripple 1.8s ease-out infinite; }
    .status-pill.warn{ background:rgba(255,181,71,.08); border-color:rgba(255,181,71,.35); color:var(--amber); }
    .status-pill.warn b{ background:var(--amber); } .status-pill.warn b::after{ border-color:var(--amber); }
    .notice{ margin:0 0 14px; padding:12px 14px; border-radius:14px; font-size:.88rem; line-height:1.5;
        background:rgba(255,181,71,.08); border:1px solid rgba(255,181,71,.3); color:var(--text); }
    .notice b{ color:var(--amber); }
    .engine-line{ color:var(--mute); font-size:.8rem; margin:10px 0 0; }

    /* ---------- headings ---------- */
    .hero{ margin:0 0 1.4rem; animation:rise .7s cubic-bezier(.2,.8,.2,1) both; }
    .main-header{ font-family:var(--display); font-weight:800; font-size:clamp(1.9rem,3.2vw,2.8rem);
        letter-spacing:-.03em; line-height:1.05; color:var(--text); margin:0 0 .5rem; }
    .section-desc{ color:var(--mute); font-size:1.02rem; max-width:62ch; margin:0 0 .9rem; line-height:1.55; }
    .tag-row{ display:flex; flex-wrap:wrap; gap:8px; }
    .tag{ padding:5px 12px; border-radius:999px; font-size:.8rem; font-weight:500; color:var(--violet-soft);
        background:rgba(124,92,255,.12); border:1px solid rgba(124,92,255,.32); }
    .tag.amber{ color:var(--amber); background:rgba(255,181,71,.10); border-color:rgba(255,181,71,.32); }
    @keyframes rise{ from{opacity:0; transform:translateY(14px)} to{opacity:1; transform:none} }

    /* ---------- the stage: interviewer + question ---------- */
    .stage{ position:relative; overflow:hidden; border-radius:22px; padding:22px 26px 26px; margin-bottom:18px;
        background:linear-gradient(160deg,var(--panel-2),var(--panel) 60%);
        border:1px solid var(--line); box-shadow:0 18px 50px -24px rgba(124,92,255,.55); }
    .stage::before{ content:""; position:absolute; top:-40%; left:50%; width:130%; height:150%;
        transform:translateX(-50%); pointer-events:none;
        background:radial-gradient(ellipse at 50% 0%, rgba(255,181,71,.16), transparent 62%);
        animation:spot 6s ease-in-out infinite alternate; }
    @keyframes spot{ from{opacity:.55; transform:translateX(-54%)} to{opacity:1; transform:translateX(-46%)} }
    .stage > *{ position:relative; }
    .stage-top{ display:flex; align-items:center; gap:14px; margin-bottom:18px; }
    .avatar{ position:relative; width:46px; height:46px; border-radius:50%; flex:none;
        display:grid; place-items:center; font-family:var(--display); font-weight:800; color:#0A0B14;
        background:linear-gradient(135deg,var(--amber),var(--violet-soft)); }
    .avatar::after{ content:""; position:absolute; inset:-5px; border-radius:50%;
        border:2px solid var(--amber); opacity:0; animation:ripple 2.2s ease-out infinite; }
    .who{ display:flex; flex-direction:column; gap:2px; min-width:0; }
    .who b{ font-family:var(--display); font-size:1.05rem; }
    .who span{ color:var(--mute); font-size:.82rem; }
    .wave{ margin-left:auto; display:flex; align-items:center; gap:3px; height:38px; }
    .wave i{ display:block; width:3px; height:100%; border-radius:3px; transform-origin:center;
        background:linear-gradient(var(--violet-soft),var(--amber));
        animation:eq var(--t,1s) ease-in-out var(--d,0s) infinite; }
    @keyframes eq{ 0%,100%{transform:scaleY(.18)} 50%{transform:scaleY(var(--h,1))} }
    @keyframes ripple{ 0%{transform:scale(.85); opacity:.7} 100%{transform:scale(1.5); opacity:0} }
    .stage-q{ font-family:var(--display); font-weight:500; font-size:clamp(1.15rem,1.9vw,1.55rem);
        line-height:1.4; letter-spacing:-.01em; margin:0; color:var(--text); }
    .stage-q span{ display:inline-block; opacity:0; filter:blur(6px); transform:translateY(6px);
        animation:word .5s ease-out forwards; animation-delay:calc(var(--i) * 45ms); margin-right:.28em; }
    @keyframes word{ to{opacity:1; filter:none; transform:none} }

    /* ---------- score ring ---------- */
    .ring-wrap{ display:flex; flex-direction:column; align-items:center; gap:10px; padding:6px 0 14px; }
    .ring{ --c:var(--mint); --size:168px; width:var(--size); height:var(--size); border-radius:50%;
        display:grid; place-items:center; position:relative;
        background:conic-gradient(var(--c) calc(var(--v) * 1%), rgba(154,156,196,.14) 0);
        animation:fill 1.5s cubic-bezier(.2,.8,.2,1) forwards;
        filter:drop-shadow(0 0 18px color-mix(in srgb, var(--c) 45%, transparent)); }
    .ring.mid{ --c:var(--amber) } .ring.low{ --c:var(--coral) } .ring.sm{ --size:128px }
    .ring::before{ content:""; position:absolute; inset:11px; border-radius:50%; background:var(--panel); }
    .ring-in{ position:relative; text-align:center; line-height:1; counter-reset:n var(--v); }
    .ring-in strong{ font-family:var(--display); font-weight:800; font-size:2.6rem; letter-spacing:-.04em; }
    .ring.sm .ring-in strong{ font-size:2rem }
    .ring-in strong::after{ content:counter(n); }
    .ring-in small{ display:block; margin-top:4px; color:var(--mute); font-size:.78rem; }
    .ring-label{ color:var(--mute); font-size:.88rem; font-weight:500; }
    @keyframes fill{ from{--v:0} to{--v:var(--p)} }

    /* ---------- STAR rows ---------- */
    .star-row{ display:flex; gap:12px; padding:12px 14px; margin-bottom:10px; border-radius:14px;
        background:var(--panel); border:1px solid var(--line); border-left:3px solid var(--k);
        animation:rise .5s ease-out both; animation-delay:calc(var(--i) * 120ms + .5s); }
    .star-badge{ flex:none; min-width:34px; height:28px; padding:0 8px; display:grid; place-items:center;
        border-radius:8px; font-family:var(--display); font-weight:800; font-size:.8rem; color:#0A0B14; background:var(--k); }
    .star-row p{ margin:0; font-size:.92rem; line-height:1.5; color:var(--text); }
    .star-row small{ display:block; color:var(--mute); font-size:.75rem; margin-bottom:2px; }

    .tip{ margin-top:14px; padding:14px 16px; border-radius:14px; font-size:.92rem; line-height:1.5;
        background:linear-gradient(120deg,rgba(255,181,71,.14),rgba(255,181,71,.03));
        border:1px solid rgba(255,181,71,.35); animation:rise .5s ease-out 1s both; }
    .tip b{ color:var(--amber); }

    /* ---------- empty state ---------- */
    .empty{ text-align:center; padding:34px 20px; border-radius:20px; border:1.5px dashed var(--line);
        background:rgba(18,20,42,.6); }
    .empty .em-ic{ font-size:2.2rem; display:inline-block; animation:float 3s ease-in-out infinite; }
    .empty h4{ font-family:var(--display); margin:.6rem 0 .2rem; font-size:1.1rem; }
    .empty p{ margin:0; color:var(--mute); font-size:.9rem; }
    @keyframes float{ 0%,100%{transform:translateY(0)} 50%{transform:translateY(-7px)} }

    /* ---------- skill chips & result panels ---------- */
    .panel{ padding:18px 20px; border-radius:20px; background:var(--panel); border:1px solid var(--line); }
    .panel h4{ font-family:var(--display); margin:0 0 12px; font-size:1.05rem; }
    .chips{ display:flex; flex-wrap:wrap; gap:8px; }
    .chip{ padding:6px 12px; border-radius:10px; font-size:.84rem; font-weight:500;
        color:var(--k); background:color-mix(in srgb, var(--k) 12%, transparent);
        border:1px solid color-mix(in srgb, var(--k) 38%, transparent);
        animation:pop .45s cubic-bezier(.2,1.4,.4,1) both; animation-delay:calc(var(--i) * 55ms + .3s); }
    @keyframes pop{ from{opacity:0; transform:scale(.6)} to{opacity:1; transform:none} }

    .profile{ display:flex; align-items:center; gap:18px; padding:20px 22px; border-radius:20px; margin:6px 0 18px;
        background:linear-gradient(130deg,rgba(124,92,255,.22),rgba(18,20,42,.9) 55%);
        border:1px solid rgba(124,92,255,.4); }
    .profile .avatar{ width:56px; height:56px; }
    .profile b{ font-family:var(--display); font-size:1.25rem; display:block; }
    .profile span{ color:var(--mute); font-size:.9rem; }

    /* ---------- native widgets ---------- */
    [data-testid="stTextArea"] textarea,[data-testid="stTextInput"] input{
        background:var(--panel); border:1px solid var(--line); border-radius:16px; color:var(--text);
        padding:14px 16px; line-height:1.55; transition:border-color .2s, box-shadow .2s; }
    [data-testid="stTextArea"] textarea:focus,[data-testid="stTextInput"] input:focus{
        border-color:var(--violet); box-shadow:0 0 0 4px rgba(124,92,255,.22), 0 0 28px rgba(124,92,255,.25); }
    [data-baseweb="select"] > div{ background:var(--panel); border-radius:14px; border-color:var(--line); }

    .stButton > button{ border-radius:14px; padding:.65rem 1.1rem; font-weight:600; position:relative; overflow:hidden;
        background:var(--panel); color:var(--text); border:1px solid var(--line);
        transition:transform .15s, border-color .2s, box-shadow .2s; }
    .stButton > button:hover{ border-color:var(--violet); transform:translateY(-2px); }
    .stButton > button:active{ transform:translateY(0) scale(.98); }
    .stButton > button[kind="primary"]{
        background:linear-gradient(135deg,#7C5CFF,#5B3FE0); border:none; color:#fff;
        box-shadow:0 10px 26px -10px rgba(124,92,255,.9); }
    .stButton > button[kind="primary"]::after{ content:""; position:absolute; top:0; left:-60%; width:40%; height:100%;
        background:linear-gradient(100deg,transparent,rgba(255,255,255,.35),transparent); transform:skewX(-20deg); }
    .stButton > button[kind="primary"]:hover::after{ left:130%; transition:left .7s ease; }
    .stButton > button:focus-visible{ outline:2px solid var(--amber); outline-offset:2px; }

    [data-testid="stFileUploader"] section{ background:var(--panel); border:1.5px dashed rgba(124,92,255,.5);
        border-radius:18px; transition:box-shadow .2s, background .2s; }
    [data-testid="stFileUploader"] section:hover{ background:var(--panel-2); box-shadow:0 0 30px rgba(124,92,255,.25); }

    [data-testid="stAlert"]{ border-radius:14px; border:1px solid var(--line); }
    [data-testid="stMetric"]{ background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:14px 18px; }
    [data-testid="stMetricValue"]{ font-family:var(--display); font-weight:800; }
    [data-testid="stSpinner"] svg{ stroke:var(--amber); }
    hr{ border-color:var(--line) !important; }

    /* ---------- guided interview: stepper, dimension bars, suggestions ---------- */
    .stepper{ display:flex; align-items:center; flex-wrap:wrap; row-gap:8px; margin:0 0 1.5rem; }
    .step{ display:flex; align-items:center; gap:8px; color:var(--mute); font-size:.85rem; font-weight:500; }
    .step .dot{ width:28px; height:28px; border-radius:50%; display:grid; place-items:center; font-size:.76rem;
        font-weight:700; border:1.5px solid var(--line); background:var(--panel); }
    .step.done{ color:var(--text); }
    .step.done .dot{ background:var(--mint); border-color:var(--mint); color:#0A0B14; }
    .step.active{ color:var(--text); font-weight:600; }
    .step.active .dot{ background:var(--violet); border-color:var(--violet); color:#fff;
        box-shadow:0 0 0 4px rgba(124,92,255,.25); animation:beat 1.8s ease-in-out infinite; }
    .step-line{ flex:1; min-width:16px; max-width:64px; height:2px; margin:0 10px; border-radius:2px;
        background:var(--line); position:relative; overflow:hidden; }
    .step-line.done::after{ content:""; position:absolute; inset:0; background:var(--mint);
        transform-origin:left; animation:grow .6s ease-out both; }
    @keyframes beat{ 50%{ box-shadow:0 0 0 9px rgba(124,92,255,.07) } }
    @keyframes grow{ from{ transform:scaleX(0) } to{ transform:scaleX(1) } }

    .dim{ margin-bottom:14px; }
    .dim-top{ display:flex; justify-content:space-between; font-size:.9rem; margin-bottom:6px; }
    .dim-top b{ font-family:var(--display); }
    .dim-track{ height:10px; border-radius:10px; background:rgba(154,156,196,.14); overflow:hidden; }
    .dim-fill{ height:100%; width:var(--w); border-radius:10px; transform-origin:left;
        background:linear-gradient(90deg, var(--k), color-mix(in srgb, var(--k) 55%, white));
        animation:grow .9s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--i) * 90ms); }

    .sug{ display:flex; gap:12px; padding:14px 16px; margin-bottom:10px; border-radius:14px;
        background:var(--panel); border:1px solid var(--line); border-left:3px solid var(--amber);
        animation:rise .5s ease-out both; animation-delay:calc(var(--i) * 90ms); }
    .sug .ic{ flex:none; font-size:1.1rem; line-height:1.4; }
    .sug p{ margin:0; font-size:.93rem; line-height:1.55; }
    .plain{ margin:0; padding-left:1.1rem; }
    .plain li{ margin-bottom:7px; font-size:.92rem; line-height:1.5; }
    .readiness{ display:inline-block; margin-top:2px; padding:5px 14px; border-radius:999px; font-size:.85rem; font-weight:600;
        color:var(--k); background:color-mix(in srgb, var(--k) 12%, transparent);
        border:1px solid color-mix(in srgb, var(--k) 40%, transparent); }

    @media (prefers-reduced-motion: reduce){
        *,*::before,*::after{ animation-duration:.01ms !important; animation-iteration-count:1 !important; transition:none !important; }
        .stage-q span,.chip,.star-row,.tip{ opacity:1 !important; filter:none !important; }
    }
    @media (max-width:640px){
        .stage{ padding:18px } .wave{ display:none }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# component builders (return HTML; render with st.markdown(..., unsafe_allow_html=True))
# ----------------------------------------------------------------------------
def sidebar_brand() -> str:
    bars = "".join(f"<i style='height:{h}%'></i>" for h in (45, 90, 60, 100, 50))
    return _h(f"""
        <div class='brand'><div class='brand-mark'>{bars}</div>
        <h2 class='brand-title'>PrepPulse AI</h2></div>
        <p class='brand-sub'>Interview intelligence, rehearsed live</p>""")


def sidebar_status(engine: str = "Gemini 2.5 Flash", live: bool = True) -> str:
    pill = ("<span class='status-pill'><b></b>Interviewer online</span>" if live
            else "<span class='status-pill warn'><b></b>Demo mode</span>")
    return _h(f"{pill}<p class='engine-line'>Engine: <strong>{_esc(engine)}</strong></p>")


def notice(text: str, title: str = "Heads up") -> str:
    return _h(f"<div class='notice'><b>{_esc(title)}:</b> {_esc(text)}</div>")


def hero(title: str, desc: str = "", tags=None) -> str:
    tag_html = ""
    if tags:
        tag_html = "<div class='tag-row'>" + "".join(
            f"<span class='tag{' amber' if i % 2 else ''}'>{_esc(t)}</span>" for i, t in enumerate(tags)
        ) + "</div>"
    desc_html = f"<p class='section-desc'>{_esc(desc)}</p>" if desc else ""
    return _h(f"<div class='hero'><h1 class='main-header'>{_esc(title)}</h1>{desc_html}{tag_html}</div>")


def interviewer_card(question: str, number: int = 1, role: str = "") -> str:
    # waveform: varied heights/speeds so it reads as speech, not a loader
    pattern = [.5, .9, .4, 1, .7, .3, .85, .6, 1, .45, .75, .35, .95, .55, .8, .4, 1, .6, .3, .7]
    bars = "".join(
        f"<i style='--h:{h};--d:{(i * 0.07) % 0.9:.2f}s;--t:{0.8 + (i % 5) * 0.12:.2f}s'></i>"
        for i, h in enumerate(pattern)
    )
    words = "".join(f"<span style='--i:{min(i, 60)}'>{_esc(w)}</span>" for i, w in enumerate(str(question).split()))
    sub = f"Question {number}" + (f" for {_esc(role)}" if role else "")
    return _h(f"""
        <div class='stage'>
          <div class='stage-top'>
            <div class='avatar'>AI</div>
            <div class='who'><b>Interviewer</b><span>{sub}</span></div>
            <div class='wave'>{bars}</div>
          </div>
          <p class='stage-q'>{words}</p>
        </div>""")


def score_ring(score, label: str = "Overall score", small: bool = False) -> str:
    s = _clamp_score(score)
    tone = "" if s >= 75 else "mid" if s >= 50 else "low"
    size = " sm" if small else ""
    return _h(f"""
        <div class='ring-wrap'>
          <div class='ring {tone}{size}' style='--p:{s}'>
            <div class='ring-in'><strong></strong><small>out of 100</small></div>
          </div>
          <div class='ring-label'>{_esc(label)}</div>
        </div>""")


def star_breakdown(breakdown: dict) -> str:
    rows = [
        ("S/T", "Situation and task", breakdown.get("situation_task", "N/A"), "var(--violet-soft)"),
        ("A", "Action", breakdown.get("action", "N/A"), "var(--amber)"),
        ("R", "Result", breakdown.get("result", "N/A"), "var(--mint)"),
    ]
    out = ""
    for i, (badge, name, text, color) in enumerate(rows):
        out += (f"<div class='star-row' style='--k:{color};--i:{i}'><div class='star-badge'>{badge}</div>"
                f"<div><small>{name}</small><p>{_esc(text)}</p></div></div>")
    return _h(out)


def tip_card(text: str) -> str:
    return _h(f"<div class='tip'><b>Try this next:</b> {_esc(text)}</div>")


def skill_chips(skills, kind: str = "match") -> str:
    color = "var(--mint)" if kind == "match" else "var(--coral)"
    chips = "".join(
        f"<span class='chip' style='--k:{color};--i:{min(i, 30)}'>{_esc(s)}</span>" for i, s in enumerate(skills)
    ) or "<span class='ring-label'>Nothing here</span>"
    return f"<div class='chips'>{chips}</div>"


def skill_panel(title: str, skills, kind: str = "match") -> str:
    return _h(f"<div class='panel'><h4>{_esc(title)}</h4>{skill_chips(skills, kind)}</div>")


def empty_state(icon: str, title: str, text: str) -> str:
    return _h(f"<div class='empty'><span class='em-ic'>{icon}</span><h4>{_esc(title)}</h4><p>{_esc(text)}</p></div>")


def profile_card(role: str, level: str) -> str:
    initials = "".join(w[0] for w in str(role).split()[:2]).upper() or "PP"
    return _h(f"""
        <div class='profile'><div class='avatar'>{_esc(initials)}</div>
        <div><b>{_esc(level)} {_esc(role)}</b><span>Questions will be tuned to this profile.</span></div></div>""")


# ----------------------------------------------------------------------------
# guided interview components
# ----------------------------------------------------------------------------
def _tone(score) -> str:
    s = _clamp_score(score)
    return "var(--mint)" if s >= 75 else "var(--amber)" if s >= 50 else "var(--coral)"


def stepper(current: int, labels) -> str:
    """Progress steps. Steps before `current` are done, `current` is highlighted."""
    parts = []
    for i, label in enumerate(labels):
        state = "done" if i < current else "active" if i == current else ""
        mark = "&#10003;" if i < current else str(i + 1)
        parts.append(f"<div class='step {state}'><span class='dot'>{mark}</span>{_esc(label)}</div>")
        if i < len(labels) - 1:
            parts.append(f"<div class='step-line {'done' if i < current else ''}'></div>")
    return _h(f"<div class='stepper'>{''.join(parts)}</div>")


def dimension_bars(dims) -> str:
    """dims: list of (label, score) pairs."""
    rows = ""
    for i, (label, score) in enumerate(dims):
        s = _clamp_score(score)
        rows += (f"<div class='dim'><div class='dim-top'><span>{_esc(label)}</span><b>{s}</b></div>"
                 f"<div class='dim-track'><div class='dim-fill' style='--w:{s}%;--k:{_tone(s)};--i:{i}'></div></div></div>")
    return _h(rows)


def suggestion_cards(items) -> str:
    icons = ["💡", "🎯", "🛠️", "📚", "🗣️", "🔁", "🚀"]
    rows = "".join(
        f"<div class='sug' style='--i:{i}'><span class='ic'>{icons[i % len(icons)]}</span><p>{_esc(t)}</p></div>"
        for i, t in enumerate(items))
    return _h(rows)


def bullet_panel(title: str, items) -> str:
    lis = "".join(f"<li>{_esc(t)}</li>" for t in items) or "<li>Nothing to show yet</li>"
    return _h(f"<div class='panel'><h4>{_esc(title)}</h4><ul class='plain'>{lis}</ul></div>")


def readiness_badge(label: str, score) -> str:
    return _h(f"<span class='readiness' style='--k:{_tone(score)}'>{_esc(label)}</span>")
