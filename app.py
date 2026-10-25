from pathlib import Path
import json
import html
import re
import streamlit as st
from config import Budget
from agents.recognizer import recognize
from agents.matcher import match
from agents.swap_chef import suggest
from agents.recipe_matcher import recommend_recipes
from agents.wine_explainer import explain_pairings
from agents.critic import critic
from tools.nutrition import compute
from tools.grocery import build
from backend_client import recognize_with_backend, calculate_with_backend
from schemas import Recognition, IngredientEstimate
from tools.wine_pairing import load_wine_catalog, profile_dish, rank_wines

st.set_page_config(page_title="HomeDish · your food, your way", page_icon="🍲", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
:root{--ink:#24312d;--muted:#718079;--cream:#fbf8f1;--paper:#fffdf9;--sage:#dce9df;--green:#2f6f57;--coral:#db654c;--yellow:#f5e8bd;--line:#e8e3d9}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:var(--ink)}.stApp{background:var(--cream)}[data-testid="stHeader"]{background:transparent}[data-testid="stSidebar"]{background:#f3efe6;border-right:1px solid var(--line)}
h1,h2,h3{font-family:'Playfair Display',serif!important;color:var(--ink)!important;letter-spacing:-.025em}h1{font-size:3rem!important;line-height:1.05!important}h2{font-size:2rem!important}.brand{padding:4px 0 28px}.brand-mark{display:inline-grid;place-items:center;width:42px;height:42px;border-radius:14px;background:var(--coral);color:white;font-size:23px;margin-right:10px;vertical-align:middle}.brand-name{font-weight:700;font-size:21px;letter-spacing:-.04em;vertical-align:middle}.brand-sub{color:var(--muted);font-size:12px;margin:9px 0 0 54px}.eyebrow{color:var(--coral);font-size:11px;text-transform:uppercase;letter-spacing:.14em;font-weight:700;margin-bottom:8px}
.hero{background:linear-gradient(115deg,#e5efe5 0%,#f8f0df 65%,#f5dfd5 100%);border-radius:26px;padding:34px 38px;min-height:205px;position:relative;overflow:hidden}.hero:after{content:'✦';position:absolute;right:42px;top:25px;color:#c3aa73;font-size:100px;opacity:.24}.hero p{color:#5f6d66;max-width:580px;font-size:16px;line-height:1.6}.section-label{display:flex;justify-content:space-between;align-items:baseline;margin:29px 0 13px}.section-label h2{margin:0!important;font-size:25px!important}.section-label span{color:var(--coral);font-size:12px;font-weight:700}.stat{background:var(--paper);border:1px solid var(--line);border-radius:17px;padding:18px 19px;min-height:105px}.stat-label{color:var(--muted);font-size:12px;font-weight:600}.stat-value{font-size:26px;font-weight:700;margin-top:9px;letter-spacing:-.05em}.stat-note{color:var(--green);font-size:11px;margin-top:3px}
.recipe-card{background:var(--paper);border:1px solid var(--line);border-radius:19px;padding:19px;min-height:181px;box-shadow:0 8px 24px rgba(72,56,31,.035)}.recipe-emoji{font-size:34px;margin-bottom:11px}.recipe-card h3{font-family:'DM Sans',sans-serif!important;font-size:16px!important;margin:0 0 7px}.recipe-card p{color:var(--muted);font-size:12px;line-height:1.55;min-height:36px}.tag{display:inline-block;background:var(--sage);color:var(--green);padding:4px 8px;border-radius:20px;font-size:10px;font-weight:700;margin:2px 3px 0 0}.planner-day{background:var(--paper);border:1px solid var(--line);border-radius:15px;padding:14px;min-height:140px}.planner-day.active{border:2px solid var(--coral)}.day-name{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-weight:700}.day-date{font-size:21px;font-weight:700;margin:2px 0 12px}.meal-pill{background:#f6ebe4;color:#825347;border-radius:9px;padding:7px 8px;font-size:11px;margin-top:7px}.meal-pill.green{background:#e5f0e5;color:#477157}.tip{background:#fff6da;border-radius:16px;padding:15px 17px;color:#806d3e;font-size:12px;line-height:1.5}.stButton>button{border-radius:11px;border:0;background:var(--coral);color:white;font-weight:700;padding:.55rem 1rem}.stButton>button:hover{background:#bd513b;color:white}[data-testid="stMetric"]{background:var(--paper);border:1px solid var(--line);border-radius:15px;padding:13px}.stTabs [data-baseweb="tab-list"]{gap:9px}.stTabs [data-baseweb="tab"]{background:#f0ece3;border-radius:10px;padding:8px 15px;border:0}.stTabs [aria-selected="true"]{background:var(--green)!important;color:white!important}.disclaimer{color:#87938d;font-size:11px;border-top:1px solid var(--line);padding-top:15px;margin-top:25px}.ingredient-head{display:grid;grid-template-columns:3fr 1.1fr 1.1fr .8fr 2fr;gap:10px;padding:0 16px 8px;color:#987c6d;font-size:10px;font-weight:700;letter-spacing:.11em;text-transform:uppercase}.ingredient-row{background:#fff8ef;border:1px solid #ead8c9;border-radius:16px;padding:9px 12px;margin:7px 0;box-shadow:0 5px 14px rgba(105,69,42,.035)}.ingredient-row [data-testid="stVerticalBlock"]{gap:.2rem}.ingredient-note{background:#f1e7dc;border-radius:12px;padding:11px 14px;color:#7d675b;font-size:12px;margin:8px 0 13px}.ingredient-row + div [data-testid="stVerticalBlockBorderWrapper"]{background:#fff8ef;border-color:#ead8c9;border-radius:16px}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
.recommendation-card{background:#fffdf9;border:1px solid #eadfd2;border-radius:22px;padding:24px 26px;margin:8px 0 12px;box-shadow:0 10px 28px rgba(88,61,39,.05)}
.recommendation-kicker{color:#db654c;font-size:10px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;margin-bottom:7px}.recommendation-card h3{font-family:'Playfair Display',serif!important;font-size:26px!important;margin:0 0 7px}.recommendation-card p{color:#68756e;font-size:13px;line-height:1.55;margin:4px 0 15px}.recommendation-change{background:#f7f0e8;border-radius:12px;padding:11px 14px;margin:8px 0;color:#46554e;font-size:13px}.recommendation-change strong{color:#2f6f57}.recommendation-change small{display:block;color:#8b7869;font-size:11px;margin-top:4px}.step-row{display:flex;gap:12px;align-items:flex-start;padding:9px 0;border-bottom:1px solid #eee6dc;color:#4a5650;font-size:13px;line-height:1.45}.step-number{display:grid;place-items:center;min-width:24px;height:24px;border-radius:50%;background:#dce9df;color:#2f6f57;font-weight:700;font-size:11px}.ingredient-chip{display:inline-block;padding:6px 10px;border-radius:18px;background:#f1e7dc;color:#765c4c;font-size:11px;margin:3px 4px 3px 0}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
:root{--ink:#182a27;--muted:#6d7a73;--cream:#f5f4ef;--paper:#fffefa;--sage:#d5e6dc;--green:#173f38;--green-2:#286454;--coral:#e4684e;--yellow:#f4e8bf;--line:#dddeda}
.stApp{background:#f5f4ef}.main .block-container{max-width:1440px;padding:2.4rem 4.5rem 5rem}.stAppViewContainer{background:#f5f4ef}[data-testid="stSidebar"]{background:#173f38;border-right:0}[data-testid="stSidebar"] *{color:#edf3ec}[data-testid="stSidebar"] hr{border-color:#356257}.brand{padding:5px 3px 30px}.brand-mark{background:#e4684e;box-shadow:0 7px 18px #0c282455}.brand-name{color:#fff}.brand-sub{color:#a9c0b6}.stRadio label{color:#c7d8d0!important}.stRadio [data-baseweb="radio"]{padding:8px 10px;border-radius:9px}.stRadio [data-baseweb="radio"]:has(input:checked){background:#2a5b50}.stRadio [data-baseweb="radio"] div:first-child{display:none}.stRadio [data-baseweb="radio"] label{font-weight:600}
h1{font-size:3.45rem!important;color:#182a27!important}h2{font-size:1.85rem!important}.eyebrow{color:#d85d45}.hero{background:linear-gradient(108deg,rgba(20,57,50,.98) 0%,rgba(24,72,61,.92) 52%,rgba(24,72,61,.67) 100%),url('https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=1500&q=80') center/cover;border-radius:18px;padding:45px 48px;min-height:270px;box-shadow:0 18px 40px rgba(19,57,50,.16)}.hero h1{color:#fff!important;font-size:3.55rem!important}.hero p{color:#d8e5dd;max-width:560px}.hero .eyebrow{color:#f4c0a6}.section-label{margin:37px 0 15px;border-bottom:1px solid #dfe1dc;padding-bottom:10px}.section-label h2{color:#183d36!important;font-family:'DM Sans',sans-serif!important;font-size:1.2rem!important;font-weight:700;letter-spacing:-.02em}.section-label span{color:#d85d45;text-transform:uppercase;letter-spacing:.1em;font-size:10px}
.recipe-card{border-radius:13px;background:#fffefa;border:1px solid #dedfd9;padding:17px;min-height:174px;box-shadow:0 8px 20px rgba(31,47,40,.045)}.recipe-card h3{font-family:'DM Sans',sans-serif!important;font-size:17px!important;color:#183d36!important}.recipe-card p{color:#77837c}.stImage img{border-radius:13px 13px 0 0;max-height:185px;object-fit:cover;filter:saturate(.94)}.stImage{margin-bottom:-10px}.tag{background:#e1eee6;color:#286454;border-radius:6px;padding:4px 7px}.stat{border-radius:12px;background:#fffefa;border-color:#dedfd9;box-shadow:0 8px 20px rgba(31,47,40,.035)}.planner-day{border-radius:12px;background:#fffefa;border-color:#dedfd9}.planner-day.active{border:2px solid #e4684e}.meal-pill{border-radius:6px}.meal-pill.green{background:#e1eee6;color:#286454}
.stButton>button{background:#173f38;border-radius:8px;border:1px solid #173f38;box-shadow:none}.stButton>button:hover{background:#286454;color:#fff}.stDownloadButton>button,.stLinkButton>button{border-radius:8px;border:1px solid #b9cfc3;background:#fffefa;color:#173f38}.stTextInput input,.stNumberInput input,.stSelectbox div[data-baseweb="select"]>div{background:#fffefa;border-color:#d8ddd8;border-radius:8px}.stTabs [data-baseweb="tab"]{background:transparent;border-radius:6px;color:#68766e}.stTabs [aria-selected="true"]{background:#173f38!important;color:#fff!important}.recommendation-card{border-radius:14px;background:#fffefa;border-color:#dedfd9}.recommendation-change{background:#edf3ed;border-radius:8px}.tip{border-radius:10px}.ingredient-note{border-radius:10px}.how-about-card{border:1px solid #d7ded8;border-radius:15px;background:#fffefa;overflow:hidden;box-shadow:0 10px 24px rgba(31,47,40,.06);min-height:355px}.how-about-card h3{font-family:'DM Sans',sans-serif!important;color:#173f38!important;font-size:19px!important;line-height:1.1;margin:0 0 8px}.how-about-body{padding:16px 17px 18px}.how-about-source{color:#d85d45;font-size:9px;font-weight:800;letter-spacing:.11em;text-transform:uppercase;margin-bottom:7px}.how-about-card p{color:#62726a;font-size:12px;line-height:1.5;margin:7px 0 11px}.how-about-label{color:#173f38;font-size:10px;text-transform:uppercase;letter-spacing:.1em;font-weight:800;margin-top:12px}.how-about-chip{display:inline-block;background:#e1eee6;color:#286454;border-radius:99px;padding:5px 8px;font-size:10px;margin:4px 4px 0 0}.how-about-angle{background:#f2f4ee;border-left:3px solid #e4684e;border-radius:0 8px 8px 0;padding:9px 10px;color:#52625a;font-size:11px;line-height:1.45;margin-top:6px}
.wine-style-card{border:1px solid #705a39;border-radius:16px;background:linear-gradient(135deg,#2c241d,#1b2020);padding:18px 20px;margin:16px 0 20px;box-shadow:0 12px 28px rgba(0,0,0,.16)}.wine-style-kicker{color:#d7fa72;font-size:10px;text-transform:uppercase;letter-spacing:.15em;font-weight:800}.wine-style-card h3{color:#f7e6bc!important;font-size:24px!important;margin:8px 0 7px}.wine-style-card p{color:#c9c0b3;font-size:12px;line-height:1.55;margin:0}.wine-card{border:1px solid #493c32;border-radius:16px;background:linear-gradient(145deg,#241f1d,#171b1b);min-height:300px;padding:19px;box-shadow:0 14px 30px rgba(0,0,0,.14)}.wine-card h3{color:#f7e6bc!important;font-family:'DM Sans',sans-serif!important;font-size:18px!important;line-height:1.1;margin:8px 0}.wine-card p{color:#bcb6ad;font-size:12px;line-height:1.5}.wine-card-meta{color:#9bded2;font-size:10px;letter-spacing:.06em;text-transform:uppercase}.wine-rating{color:#d7fa72;font-weight:700;font-size:12px;margin:8px 0}.wine-chip{display:inline-block;background:#3b3026;color:#f0d29d;border:1px solid #66503b;border-radius:99px;padding:5px 8px;font-size:10px;margin:3px 4px 0 0}.wine-why{border-left:3px solid #8dd6f6;background:#282525;border-radius:0 8px 8px 0;padding:9px 10px;color:#d8dfdb;font-size:11px;line-height:1.45;margin-top:10px}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.ingredient-stage{background:#111315;border-radius:25px;padding:22px 22px 13px;margin:14px 0 18px;box-shadow:0 18px 45px rgba(20,20,20,.16);border:1px solid #2c3033}.ingredient-stage-title{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:18px}.ingredient-stage-title h3{font-family:'DM Sans',sans-serif!important;color:#fff!important;font-size:20px!important;margin:0}.ingredient-stage-title p{color:#9da6aa;font-size:11px;margin:4px 0 0}.ingredient-mode{border:1px solid #555b60;border-radius:100px;color:#fff;font-size:10px;letter-spacing:.12em;padding:7px 10px;text-transform:uppercase}.ingredient-head{background:#1d2022;border:0;border-radius:14px;padding:12px 16px;color:#d7e5df;letter-spacing:.15em}[data-testid="stVerticalBlock"]:has(.ingredient-scope) [data-testid="stVerticalBlockBorderWrapper"]{background:#17191b!important;border:1px solid #32373b!important;border-radius:16px!important;box-shadow:none!important;margin:7px 0}[data-testid="stVerticalBlock"]:has(.ingredient-scope) [data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(3n){border-color:#5d55db!important}[data-testid="stVerticalBlock"]:has(.ingredient-scope) [data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(3n+1){border-color:#31c7bb!important}[data-testid="stVerticalBlock"]:has(.ingredient-scope) [data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(3n+2){border-color:#ea6e91!important}[data-testid="stVerticalBlock"]:has(.ingredient-scope) [data-testid="stVerticalBlockBorderWrapper"] input{background:#222629!important;border:1px solid #444b50!important;color:#fff!important;border-radius:9px!important}[data-testid="stVerticalBlock"]:has(.ingredient-scope) [data-testid="stVerticalBlockBorderWrapper"] input:focus{border-color:#64e7d5!important;box-shadow:0 0 0 1px #64e7d5!important}[data-testid="stVerticalBlock"]:has(.ingredient-scope) [data-testid="stVerticalBlockBorderWrapper"] label{color:#aab4b8!important}[data-testid="stVerticalBlock"]:has(.ingredient-scope) [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] label{color:#fff!important}[data-testid="stVerticalBlock"]:has(.ingredient-scope) .ingredient-row{background:transparent;border:0;box-shadow:none;margin:0;padding:0}[data-testid="stVerticalBlock"]:has(.ingredient-scope) .ingredient-note{background:#262b2d;color:#d8e4df;border-radius:13px}[data-testid="stVerticalBlock"]:has(.ingredient-scope) .tip{background:#24282a;color:#c5d0cc;border:1px solid #394145}[data-testid="stVerticalBlock"]:has(.ingredient-scope) [data-baseweb="input"]{background:#222629!important}[data-testid="stVerticalBlock"]:has(.ingredient-scope) [data-baseweb="input"] input{background:transparent!important}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Home landing page: dark editorial surfaces, bright food-led accents, and a calmer rhythm. */
body:has(.landing-page) .stApp,body:has(.landing-page) .stAppViewContainer{background:#111313!important;color:#f4f2ed}
body:has(.landing-page) .main .block-container{max-width:1600px;padding:0 2.8rem 5rem}
body:has(.landing-page) .main [data-testid="stMarkdownContainer"]{color:#f4f2ed}
body:has(.landing-page) [data-testid="stHeader"]{background:#111313}
body:has(.landing-page) [data-testid="stSidebar"]{background:#111313;border-right:1px solid #292d2e}
body:has(.landing-page) [data-testid="stSidebar"] .brand{border-bottom:1px solid #292d2e}
body:has(.landing-page) [data-testid="stSidebar"] .disclaimer{border-color:#292d2e}
.landing-page{background:#111313;color:#f4f2ed;margin:0 -2.8rem;padding:0 2.8rem 1px;overflow:hidden}
.landing-nav{min-height:76px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #2a2d2e;gap:30px}
.landing-logo{font-size:27px;line-height:1;font-weight:700;letter-spacing:-.07em;color:#fff;white-space:nowrap}.landing-logo span{color:#8dd6f6}
.landing-nav-links{display:flex;gap:34px;align-items:center;flex:1;margin-left:44px}.landing-nav-links a{color:#aeb4b2;font-size:10px;text-transform:uppercase;letter-spacing:.2em;font-weight:700;text-decoration:none}.landing-nav-links a:first-child{color:#fff}.landing-nav-links a:hover{color:#d7fa72}
.landing-nav-meta{display:flex;gap:15px;align-items:center;color:#afb8b5;font-size:10px;text-transform:uppercase;letter-spacing:.18em}.landing-pill{display:inline-block;border:1px solid #596060;border-radius:100px;padding:10px 15px;color:#f2f1ed;text-decoration:none}.landing-pill:hover{border-color:#d7fa72;color:#d7fa72}.landing-pill.blue{background:#73c6ed;color:#102126;border-color:#73c6ed}.landing-pill.blue:hover{background:#d7fa72;color:#17201d;border-color:#d7fa72}
.landing-hero{display:grid;grid-template-columns:minmax(0,1.08fr) minmax(390px,.92fr);gap:7vw;align-items:center;padding:92px 3.3vw 105px;min-height:610px;position:relative}.landing-hero:before{content:'';position:absolute;width:520px;height:520px;border-radius:50%;background:#d8fa72;filter:blur(100px);opacity:.11;left:-210px;top:120px;pointer-events:none}.landing-hero-copy{position:relative;z-index:1}.landing-eyebrow{color:#8dd6f6;font-size:11px;text-transform:uppercase;letter-spacing:.24em;font-weight:700;margin-bottom:21px}.landing-hero h1{font-family:'DM Sans',sans-serif!important;color:#f5f3ee!important;font-size:clamp(3.7rem,7.1vw,7.8rem)!important;line-height:.9!important;letter-spacing:-.085em!important;margin:0 0 29px!important;max-width:790px}.landing-hero h1 em{font-style:normal;color:#d7fa72}.landing-hero p{color:#a9b2ae;font-size:17px;line-height:1.6;max-width:570px;margin:0}.landing-hero-meta{display:flex;gap:10px;align-items:center;margin-top:30px;color:#7f8b87;font-size:11px}.landing-dot{width:7px;height:7px;background:#d7fa72;border-radius:50%;display:inline-block;box-shadow:0 0 0 5px #d7fa7219}
.landing-hero-visual{position:relative;min-height:495px}.landing-plate-image{height:470px;width:100%;border-radius:24px;background:linear-gradient(145deg,#1e2727aa,#101414aa),url('https://images.unsplash.com/photo-1467003909585-2f8a72700288?auto=format&fit=crop&w=1200&q=88') center/cover;box-shadow:0 35px 80px #00000075;transform:rotate(2deg)}.landing-plate-image:after{content:'HOME DISH';position:absolute;inset:18px;border:1px solid #ffffff42;border-radius:17px;color:#ffffffbf;font-size:10px;letter-spacing:.26em;padding:20px}
.landing-float{position:absolute;background:#232727eF;border:1px solid #ffffff2b;border-radius:16px;backdrop-filter:blur(14px);box-shadow:0 16px 40px #0008}.landing-float.main{left:-45px;bottom:26px;padding:19px 20px;width:235px}.landing-float.top{right:-20px;top:38px;padding:15px 17px;width:170px}.landing-float-kicker{font-size:9px;text-transform:uppercase;letter-spacing:.16em;color:#8dd6f6;font-weight:700}.landing-float-title{font-size:20px;font-weight:700;letter-spacing:-.04em;margin:7px 0 4px}.landing-float-copy{font-size:11px;color:#b1bab6;line-height:1.4}.landing-meter{height:6px;background:#424949;border-radius:99px;margin:13px 0 9px}.landing-meter i{display:block;width:68%;height:100%;border-radius:99px;background:linear-gradient(90deg,#d7fa72,#8dd6f6)}.landing-float-stats{display:flex;justify-content:space-between;color:#eaf0ec;font-size:11px}.landing-float-stats span:last-child{color:#d7fa72}
.landing-actions-anchor{margin:0 3.3vw -42px;position:relative;z-index:3}.landing-actions-anchor [data-testid="stHorizontalBlock"]{gap:12px}.landing-actions-anchor .stButton>button{border-radius:100px!important;min-height:48px!important;padding:0 23px!important;font-size:11px!important;letter-spacing:.1em!important;text-transform:uppercase!important;font-weight:700!important;background:#d7fa72!important;color:#17201c!important;border:1px solid #d7fa72!important}.landing-actions-anchor [data-testid="column"]:nth-child(2) .stButton>button{background:transparent!important;color:#f3f2ed!important;border-color:#656d6a!important}
.landing-marquee{border-top:1px solid #2a2d2e;border-bottom:1px solid #2a2d2e;padding:19px 3.3vw;color:#77817e;font-size:10px;text-transform:uppercase;letter-spacing:.23em;display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}.landing-marquee strong{color:#e4e9e5;font-weight:500}.landing-marquee b{color:#d7fa72;font-weight:700}
.landing-section{padding:112px 3.3vw 36px}.landing-section.dark-pad{padding-top:90px}.landing-section-head{display:flex;justify-content:space-between;gap:30px;align-items:flex-end;margin-bottom:37px}.landing-section-head h2{font-family:'DM Sans',sans-serif!important;color:#f4f2ed!important;font-size:clamp(2rem,4vw,4.2rem)!important;line-height:.96!important;letter-spacing:-.07em!important;margin:0!important;max-width:750px}.landing-section-head p{color:#8d9893;line-height:1.55;font-size:14px;max-width:340px;margin:0}.landing-kicker{color:#8dd6f6;font-size:10px;text-transform:uppercase;letter-spacing:.2em;font-weight:700;margin-bottom:13px}
.landing-feature{min-height:314px;border-radius:20px;padding:25px;position:relative;overflow:hidden;border:1px solid #ffffff25}.landing-feature h3{font-family:'DM Sans',sans-serif!important;color:#17201d!important;font-size:25px!important;line-height:1!important;letter-spacing:-.06em!important;max-width:230px;margin:85px 0 12px!important}.landing-feature p{color:#30413c;font-size:12px;line-height:1.5;max-width:245px}.landing-feature small{position:absolute;right:23px;top:22px;color:#17201d;font-size:10px;letter-spacing:.16em;font-weight:700}.landing-feature.aqua{background:#9ce6e4}.landing-feature.lilac{background:#c9b8fc}.landing-feature.lime{background:#d7fa72}.landing-feature-art{position:absolute;right:20px;top:20px;width:84px;height:84px;border-radius:50%;background:#1824221f}.landing-feature-art:before{content:'';position:absolute;inset:17px;border:1px solid #17201d8c;border-radius:50%}.landing-feature-art:after{content:'✦';position:absolute;inset:0;display:grid;place-items:center;color:#17201d;font-size:23px}.landing-feature.lilac .landing-feature-art{border-radius:16px;transform:rotate(12deg)}.landing-feature.lilac .landing-feature-art:after{content:'↗';font-size:34px}.landing-feature.lime .landing-feature-art{border-radius:50% 50% 14px 50%;transform:rotate(-18deg)}.landing-feature.lime .landing-feature-art:after{content:'03';font-size:18px}
.landing-stories{background:#191b1b;margin:75px -2.8rem 0;padding:103px 5.3vw 95px}.landing-stories-head{text-align:center}.landing-stories-head .landing-kicker{color:#d7fa72}.landing-stories-head h2{font-family:'DM Sans',sans-serif!important;color:#fff!important;font-size:clamp(2.1rem,4vw,4.2rem)!important;letter-spacing:-.07em!important;line-height:.95!important;margin:0 0 35px!important}.landing-story-card{height:326px;background:linear-gradient(145deg,#3a3d3d,#252727);border:1px solid #ffffff0d;border-radius:13px;padding:25px 23px;display:flex;flex-direction:column;justify-content:space-between;box-shadow:inset 0 1px #ffffff08}.landing-story-card p{color:#edf0ec;font-size:15px;line-height:1.45;margin:0}.landing-story-card footer{color:#fff;font-size:12px;font-weight:700}.landing-story-card footer span{display:block;color:#969e9b;font-size:10px;font-weight:400;margin-top:4px}.landing-story-note{text-align:center;color:#626b68;font-size:10px;letter-spacing:.04em;margin:34px 0 0}.landing-story-nav{display:flex;justify-content:center;align-items:center;gap:25px;margin:0 0 35px}.landing-story-nav-label{color:#dfe4df;font-size:11px;letter-spacing:.22em;text-transform:uppercase;font-weight:700}.landing-story-nav-arrow{color:#f4f4ef;font-size:25px}
.landing-culture{min-height:525px;margin:0 -2.8rem;padding:120px 5.3vw;background:linear-gradient(180deg,#191b1b99,#111313d9),url('https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=1800&q=85') center/cover;display:flex;align-items:center;justify-content:center;text-align:center}.landing-culture h2{font-family:'DM Sans',sans-serif!important;color:#fff!important;font-size:clamp(2.7rem,5vw,5.7rem)!important;line-height:.94!important;letter-spacing:-.08em!important;max-width:850px!important;margin:0 auto 24px!important}.landing-culture p{color:#d7dfdb;font-size:15px;line-height:1.55;max-width:560px;margin:0 auto}.landing-culture .landing-kicker{color:#d7fa72}
.landing-bottom-cta{padding:115px 3.3vw 125px;text-align:center;background:#111313}.landing-bottom-cta h2{font-family:'DM Sans',sans-serif!important;color:#f4f2ed!important;font-size:clamp(2.7rem,5.5vw,6.3rem)!important;line-height:.9!important;letter-spacing:-.08em!important;margin:0 auto 23px!important;max-width:900px}.landing-bottom-cta p{color:#899490;max-width:500px;margin:0 auto 27px;line-height:1.5;font-size:14px}.landing-bottom-cta .landing-kicker{color:#8dd6f6}
@media (max-width:900px){body:has(.landing-page) .main .block-container{padding:0 1rem 4rem}.landing-page{margin:0 -1rem;padding:0 1rem}.landing-nav-links,.landing-nav-meta{display:none}.landing-hero{grid-template-columns:1fr;padding:65px 1rem 75px;gap:35px}.landing-hero h1{font-size:clamp(3.5rem,15vw,6rem)!important}.landing-hero-visual{min-height:390px}.landing-plate-image{height:370px}.landing-float.main{left:12px}.landing-float.top{right:10px}.landing-actions-anchor{margin:0 1rem -38px}.landing-marquee{padding-left:1rem;padding-right:1rem}.landing-section{padding-left:1rem;padding-right:1rem}.landing-section-head{display:block}.landing-section-head p{margin-top:18px}.landing-stories,.landing-culture{margin-left:-1rem;margin-right:-1rem}.landing-stories{padding:75px 1rem}.landing-culture{padding:90px 1rem}.landing-bottom-cta{padding:85px 1rem}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stVerticalBlock"]:has(.landing-actions-anchor) [data-testid="stHorizontalBlock"]{gap:12px}
[data-testid="stVerticalBlock"]:has(.landing-actions-anchor) .stButton>button{border-radius:100px!important;min-height:48px!important;padding:0 23px!important;font-size:11px!important;letter-spacing:.1em!important;text-transform:uppercase!important;font-weight:700!important;background:#d7fa72!important;color:#17201c!important;border:1px solid #d7fa72!important}
[data-testid="stVerticalBlock"]:has(.landing-actions-anchor) [data-testid="column"]:nth-child(2) .stButton>button{background:transparent!important;color:#f3f2ed!important;border-color:#656d6a!important}
[data-testid="stVerticalBlock"]:has(.landing-stories-scope){background:#191b1b;margin:75px -2.8rem 0;padding:103px 5.3vw 95px}
[data-testid="stVerticalBlock"]:has(.landing-stories-scope) [data-testid="stHorizontalBlock"]{align-items:center}
[data-testid="stVerticalBlock"]:has(.landing-stories-scope) .stButton>button{border-radius:50%!important;background:transparent!important;border:1px solid #656d6a!important;color:#f4f4ef!important;min-height:40px!important;font-size:20px!important;padding:0!important}
@media (max-width:900px){[data-testid="stVerticalBlock"]:has(.landing-stories-scope){margin-left:-1rem;margin-right:-1rem;padding:75px 1rem}.landing-actions-anchor{margin-left:1rem;margin-right:1rem}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Shared dark product system for every utility page. Home keeps its bespoke landing composition above. */
body:not(:has(.landing-page)) .stApp,body:not(:has(.landing-page)) .stAppViewContainer,body:not(:has(.landing-page)) [data-testid="stMain"]{background:#111313!important;color:#f4f2ed}
body:not(:has(.landing-page)) .main .block-container{max-width:1440px;padding:2.8rem 4.5rem 5rem}
body:not(:has(.landing-page)) [data-testid="stHeader"]{background:#111313}
body:not(:has(.landing-page)) [data-testid="stSidebar"]{background:#171b1b;border-right:1px solid #2c3232}
body:not(:has(.landing-page)) [data-testid="stSidebar"] *{color:#eef1ed}
body:not(:has(.landing-page)) [data-testid="stSidebar"] hr{border-color:#35403e}
body:not(:has(.landing-page)) [data-testid="stSidebar"] .brand{border-bottom:1px solid #35403e;padding-bottom:26px}
body:not(:has(.landing-page)) [data-testid="stSidebar"] .brand-mark{background:#d7fa72;color:#17201d;box-shadow:0 8px 22px #d7fa7230}
body:not(:has(.landing-page)) [data-testid="stSidebar"] .brand-name{color:#f8f7f2}
body:not(:has(.landing-page)) [data-testid="stSidebar"] .brand-sub{color:#9aa8a3}
body:not(:has(.landing-page)) [data-testid="stSidebar"] .disclaimer{border-color:#35403e;color:#7e8c87}
body:not(:has(.landing-page)) h1,body:not(:has(.landing-page)) h2,body:not(:has(.landing-page)) h3,body:not(:has(.landing-page)) h4{font-family:'DM Sans',sans-serif!important;color:#f4f2ed!important;letter-spacing:-.06em!important}
body:not(:has(.landing-page)) h1{font-size:clamp(2.7rem,5vw,5rem)!important;line-height:.96!important}
body:not(:has(.landing-page)) h2{font-size:2rem!important}
body:not(:has(.landing-page)) .main [data-testid="stMarkdownContainer"]>p{color:#a9b2ae!important;line-height:1.6}
body:not(:has(.landing-page)) .eyebrow{color:#8dd6f6;font-size:10px;letter-spacing:.22em}
body:not(:has(.landing-page)) .section-label{border-bottom:1px solid #2b3231;margin-top:38px;padding-bottom:11px}
body:not(:has(.landing-page)) .section-label h2{color:#f4f2ed!important;font-size:1.15rem!important;letter-spacing:-.03em!important}
body:not(:has(.landing-page)) .section-label span{color:#d7fa72;text-transform:uppercase;letter-spacing:.14em;font-size:10px}
body:not(:has(.landing-page)) .recipe-card,body:not(:has(.landing-page)) .stat,body:not(:has(.landing-page)) .planner-day,body:not(:has(.landing-page)) [data-testid="stMetric"],body:not(:has(.landing-page)) .recommendation-card,body:not(:has(.landing-page)) .how-about-card{background:#1b2020!important;border-color:#303838!important;color:#f4f2ed;box-shadow:0 16px 35px #00000025}
body:not(:has(.landing-page)) .recipe-card h3,body:not(:has(.landing-page)) .stat-value,body:not(:has(.landing-page)) .day-date,body:not(:has(.landing-page)) .recommendation-card h3{color:#f4f2ed!important}
body:not(:has(.landing-page)) .recipe-card p,body:not(:has(.landing-page)) .stat-label,body:not(:has(.landing-page)) .day-name{color:#9da9a4}
body:not(:has(.landing-page)) .stat-note{color:#d7fa72}
body:not(:has(.landing-page)) .tag{background:#283b38;color:#a5eee1;border:1px solid #3a5b55}
body:not(:has(.landing-page)) .planner-day.active{border:2px solid #8dd6f6!important;background:#202827!important}
body:not(:has(.landing-page)) .meal-pill{background:#332c28;color:#f1b39e}
body:not(:has(.landing-page)) .meal-pill.green{background:#243f37;color:#b4efbc}
body:not(:has(.landing-page)) .tip{background:#242b29!important;border:1px solid #3c4b47;color:#d7e4df}
body:not(:has(.landing-page)) .recommendation-kicker{color:#8dd6f6}
body:not(:has(.landing-page)) .recommendation-change{background:#242c2a;color:#dce7e1;border:1px solid #34423e}
body:not(:has(.landing-page)) .how-about-card h3,body:not(:has(.landing-page)) .how-about-label{color:#f4f2ed!important}body:not(:has(.landing-page)) .how-about-card p{color:#a9b2ae!important}body:not(:has(.landing-page)) .how-about-source{color:#8dd6f6}body:not(:has(.landing-page)) .how-about-chip{background:#283b38;color:#a5eee1;border:1px solid #3a5b55}body:not(:has(.landing-page)) .how-about-angle{background:#242c2a;border-color:#d7fa72;color:#dce7e1}
body:not(:has(.landing-page)) .recommendation-change strong{color:#d7fa72}
body:not(:has(.landing-page)) .recommendation-change small{color:#9aa8a2}
body:not(:has(.landing-page)) .step-row{border-color:#303837;color:#d5dfda}
body:not(:has(.landing-page)) .step-number{background:#d7fa72;color:#17201d}
body:not(:has(.landing-page)) .ingredient-chip{background:#293837;color:#b4eee3}
body:not(:has(.landing-page)) .stImage img{border-radius:18px;filter:saturate(.9) brightness(.86)}
body:not(:has(.landing-page)) .stTextInput input,body:not(:has(.landing-page)) .stNumberInput input,body:not(:has(.landing-page)) textarea,body:not(:has(.landing-page)) .stSelectbox [data-baseweb="select"]>div,body:not(:has(.landing-page)) .stMultiSelect [data-baseweb="select"]>div{background:#1d2322!important;border-color:#3a4542!important;color:#f4f2ed!important;border-radius:10px}
body:not(:has(.landing-page)) .stSelectbox [data-baseweb="select"],body:not(:has(.landing-page)) .stMultiSelect [data-baseweb="select"]{background:#1d2322!important;border:1px solid #3a4542!important;border-radius:10px!important}
body:not(:has(.landing-page)) .stSelectbox [data-baseweb="select"]>div,body:not(:has(.landing-page)) .stMultiSelect [data-baseweb="select"]>div,body:not(:has(.landing-page)) .stSelectbox [data-baseweb="select"]>div>div,body:not(:has(.landing-page)) .stMultiSelect [data-baseweb="select"]>div>div{background:#1d2322!important;color:#dce8e2!important}
body:not(:has(.landing-page)) [data-baseweb="select"] *,body:not(:has(.landing-page)) input,body:not(:has(.landing-page)) textarea{color:#dce8e2!important}
body:not(:has(.landing-page)) input::placeholder,body:not(:has(.landing-page)) textarea::placeholder{color:#91a09a!important;opacity:1!important}
body:not(:has(.landing-page)) .stTextInput input:focus,body:not(:has(.landing-page)) .stNumberInput input:focus,body:not(:has(.landing-page)) textarea:focus,body:not(:has(.landing-page)) .stSelectbox [data-baseweb="select"]:focus-within,body:not(:has(.landing-page)) .stMultiSelect [data-baseweb="select"]:focus-within{border-color:#8dd6f6!important;box-shadow:0 0 0 1px #8dd6f6!important}
body:not(:has(.landing-page)) [data-baseweb="popover"],body:not(:has(.landing-page)) [data-baseweb="menu"],body:not(:has(.landing-page)) [role="listbox"]{background:#1d2322!important;border:1px solid #3a4542!important}
body:not(:has(.landing-page)) [role="option"]{background:#1d2322!important;color:#dce8e2!important}
body:not(:has(.landing-page)) [role="option"]:hover,body:not(:has(.landing-page)) [role="option"][aria-selected="true"]{background:#d7fa72!important;color:#17201d!important}
body:not(:has(.landing-page)) [data-testid="stFileUploaderDropzone"]{background:#1b2020;border:1px dashed #53615c;border-radius:18px}
body:not(:has(.landing-page)) [data-testid="stFileUploaderDropzone"] *{color:#d4dfda}
body:not(:has(.landing-page)) [data-testid="stCheckbox"] label,body:not(:has(.landing-page)) [data-testid="stRadio"] label{color:#dce6e1!important}
body:not(:has(.landing-page)) [data-testid="stVerticalBlockBorderWrapper"]{background:#1b2020!important;border-color:#303838!important;border-radius:16px!important}
body:not(:has(.landing-page)) .stButton>button{background:#d7fa72!important;border:1px solid #d7fa72!important;color:#17201d!important;border-radius:10px;font-weight:700}
body:not(:has(.landing-page)) .stButton>button:hover{background:#efffb1!important;border-color:#efffb1!important;color:#17201d!important}
body:not(:has(.landing-page)) .stDownloadButton>button,body:not(:has(.landing-page)) .stLinkButton>button{background:transparent!important;border:1px solid #53615c!important;color:#eff3ee!important;border-radius:10px}
body:not(:has(.landing-page)) .stTabs [data-baseweb="tab-list"]{gap:8px;border-bottom:1px solid #303837}
body:not(:has(.landing-page)) .stTabs [data-baseweb="tab"]{background:#1b2020;color:#aab5b0;border:1px solid #303837;border-radius:9px 9px 0 0}
body:not(:has(.landing-page)) .stTabs [aria-selected="true"]{background:#8dd6f6!important;color:#132126!important;border-color:#8dd6f6!important}
body:not(:has(.landing-page)) .stRadio [data-baseweb="radio"],body:not(:has(.landing-page)) [role="radio"]{padding:8px 10px;border-radius:10px}
body:not(:has(.landing-page)) .stRadio [data-baseweb="radio"]:has(input:checked),body:not(:has(.landing-page)) [role="radio"][aria-checked="true"]{background:#d7fa72!important;color:#17201d!important}
body:not(:has(.landing-page)) .stRadio [data-baseweb="radio"]:has(input:checked) label,body:not(:has(.landing-page)) [role="radio"][aria-checked="true"] label{color:#17201d!important}
body:not(:has(.landing-page)) .stRadio [data-baseweb="radio"]>div:first-child,body:not(:has(.landing-page)) [role="radio"]>div:first-child{display:none!important}
@media (max-width:900px){body:not(:has(.landing-page)) .main .block-container{padding:2rem 1rem 4rem}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Global top navigation: a quiet Arta-inspired bar shared by every page. */
[data-testid="stSidebar"]{display:none!important}
body .main .block-container{padding-top:0!important}
[data-testid="stVerticalBlock"]:has(.topbar-anchor){background:#191b1b;margin:0 -4.5rem 3.2rem;padding:0 4.5rem;border-bottom:1px solid #303434;min-height:78px;display:flex;justify-content:center}
[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="stHorizontalBlock"]{align-items:center;gap:14px;min-height:78px}
[data-testid="stVerticalBlock"]:has(.topbar-anchor) .stButton>button{background:transparent!important;border:0!important;color:#cbd2ce!important;border-radius:0!important;box-shadow:none!important;min-height:48px!important;padding:0 8px!important;font-size:10px!important;font-weight:700!important;letter-spacing:.22em!important;text-transform:uppercase!important;white-space:nowrap}
[data-testid="stVerticalBlock"]:has(.topbar-anchor) .stButton>button:hover{color:#d7fa72!important;background:transparent!important}
[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="stPopoverButton"]{background:transparent!important;border:1px solid #555e5a!important;color:#cbd2ce!important;border-radius:100px!important;min-height:40px!important;padding:0 13px!important;font-size:9px!important;font-weight:700!important;letter-spacing:.16em!important;text-transform:uppercase!important}
[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="stPopoverButton"]:hover{background:#d7fa72!important;border-color:#d7fa72!important;color:#17201d!important}
[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="column"]:nth-child(7) [data-testid="stPopoverButton"]{background:#73c6ed!important;border-color:#73c6ed!important;color:#102126!important}
[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="column"]:nth-child(7) [data-testid="stPopoverButton"]:hover{background:#d7fa72!important;border-color:#d7fa72!important;color:#17201d!important}
[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="column"]:first-child .stButton>button{font-size:29px!important;letter-spacing:-.08em!important;text-transform:lowercase!important;color:#f6f4ee!important;justify-content:flex-start}
[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="column"]:first-child .stButton>button:hover{color:#8dd6f6!important}
[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="column"]:nth-child(6) .stButton>button,[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="column"]:nth-child(7) .stButton>button{border:1px solid #555e5a!important;border-radius:100px!important;padding:0 13px!important;font-size:9px!important;letter-spacing:.16em!important}
[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="column"]:nth-child(7) .stButton>button{background:#73c6ed!important;color:#102126!important;border-color:#73c6ed!important}
[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="column"]:nth-child(7) .stButton>button:hover{background:#d7fa72!important;border-color:#d7fa72!important;color:#17201d!important}
[data-testid="stPopoverBody"]{background:#1d2322!important;border:1px solid #3a4542!important;border-radius:14px!important}
[data-testid="stPopoverBody"] label,[data-testid="stPopoverBody"] p{color:#dce8e2!important}
[data-testid="stPopoverBody"] .stButton>button{background:#273331!important;border:1px solid #3d514b!important;color:#dce8e2!important;border-radius:9px!important;letter-spacing:.08em!important}
[data-testid="stPopoverBody"] .stButton>button:hover{background:#d7fa72!important;color:#17201d!important}
@media (max-width:900px){[data-testid="stVerticalBlock"]:has(.topbar-anchor){margin:0 -1rem 2rem;padding:0 1rem}[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="stHorizontalBlock"]{gap:2px}[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="column"]:nth-child(2),[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="column"]:nth-child(4),[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="column"]:nth-child(5){display:none}[data-testid="stVerticalBlock"]:has(.topbar-anchor) [data-testid="column"]:first-child .stButton>button{font-size:23px!important}}
</style>
""", unsafe_allow_html=True)

RECIPES=[
    {"name":"Harissa salmon couscous","emoji":"🐟","description":"Warm spices, flaky salmon, and a bright herb finish","tags":["25 min","high protein"],"cuisine":"Mediterranean","diet":"High protein","image":"https://images.unsplash.com/photo-1467003909585-2f8a72700288?auto=format&fit=crop&w=900&q=85","ingredients":["2 salmon fillets","150 g couscous","1 tbsp harissa","1 lemon","parsley","cucumber"],"steps":["Rub salmon with harissa and roast until just cooked.","Fluff couscous with lemon and herbs.","Serve with cucumber and pan juices."],"nutrition":"430–520 kcal","source":"HomeDish test kitchen"},
    {"name":"Green shakshuka","emoji":"🥚","description":"Silky greens and eggs with a little feta","tags":["25 min","vegetarian"],"cuisine":"Middle Eastern","diet":"Vegetarian","image":"https://images.unsplash.com/photo-1590412200988-a436970781fa?auto=format&fit=crop&w=900&q=85","ingredients":["4 eggs","spinach","kale","1 onion","feta","whole-grain bread"],"steps":["Soften onion and wilt the greens.","Make wells and crack in the eggs.","Cover until whites set; finish with feta."],"nutrition":"320–410 kcal","source":"HomeDish test kitchen"},
    {"name":"Dal with roasted cauliflower","emoji":"🍛","description":"Comforting lentils with a golden, crisp topping","tags":["40 min","plant-based"],"cuisine":"South Asian","diet":"Vegan","image":"https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=900&q=85","ingredients":["red lentils","cauliflower","tomato","turmeric","cumin","basmati rice"],"steps":["Simmer lentils with tomato and turmeric.","Roast cauliflower with cumin.","Finish dal with herbs and serve together."],"nutrition":"410–500 kcal","source":"HomeDish test kitchen"},
    {"name":"Ginger scallion chicken","emoji":"🍗","description":"Aromatic, savory, and ready in one pan","tags":["25 min","one pan"],"cuisine":"Chinese","diet":"High protein","image":"https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=900&q=85","ingredients":["300 g chicken breast","4 scallions","20 g ginger","1 tsp sesame oil","1 tbsp soy sauce"],"steps":["Sear chicken until golden.","Add ginger, scallions, soy, and a splash of water.","Cover briefly, then slice and serve."],"nutrition":"360–430 kcal"},
    {"name":"Gochujang tofu bowls","emoji":"🥬","description":"A crisp, spicy bowl with Korean pantry staples","tags":["20 min","vegetarian"],"cuisine":"Korean","diet":"Vegetarian","image":"https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=85","ingredients":["250 g firm tofu","1 tbsp gochujang","150 g cooked rice","1 cucumber","1 carrot","sesame seeds"],"steps":["Press and crisp tofu in a hot pan.","Whisk gochujang with rice vinegar and sesame.","Layer rice, vegetables, and tofu."],"nutrition":"390–480 kcal"},
    {"name":"Plantain black bean plate","emoji":"🍌","description":"Sweet, savory, and filling without the heaviness","tags":["30 min","budget"],"cuisine":"Caribbean","diet":"Vegan","image":"https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=900&q=85","ingredients":["1 ripe plantain","200 g black beans","1 lime","1 avocado","cabbage slaw"],"steps":["Roast plantain until caramelized.","Warm beans with cumin and lime.","Serve with crunchy slaw and avocado."],"nutrition":"420–510 kcal"},
]

RECIPES += [
    {"name":"Lemony lentil salad","emoji":"🥗","description":"A bright pantry salad that gets better overnight","tags":["15 min","plant-based"],"cuisine":"Mediterranean","diet":"Vegan","image":"https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=900&q=85","ingredients":["250 g cooked lentils","1 cucumber","cherry tomatoes","1 lemon","fresh herbs","olive oil"],"steps":["Rinse lentils and chop the vegetables.","Whisk lemon, herbs, and olive oil.","Toss together and rest for ten minutes."],"nutrition":"280–360 kcal","source":"HomeDish test kitchen"},
    {"name":"Thai basil chicken","emoji":"🌿","description":"Fragrant, savory, and faster than takeout","tags":["20 min","one pan"],"cuisine":"Thai","diet":"High protein","image":"https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?auto=format&fit=crop&w=900&q=85","ingredients":["300 g ground chicken","Thai basil","garlic","chili","1 tbsp fish sauce","steamed rice"],"steps":["Fry garlic and chili until fragrant.","Brown chicken and season with fish sauce.","Fold through basil and serve with rice."],"nutrition":"390–470 kcal","source":"HomeDish test kitchen"},
    {"name":"Miso soba bowl","emoji":"🍜","description":"Nutty noodles, crisp vegetables, and a silky miso dressing","tags":["20 min","vegetarian"],"cuisine":"Japanese","diet":"Vegetarian","image":"https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=900&q=85","ingredients":["180 g soba noodles","1 tbsp white miso","edamame","cucumber","mushrooms","sesame"],"steps":["Cook soba and rinse until cool.","Whisk miso with rice vinegar and ginger.","Toss with vegetables and edamame."],"nutrition":"370–450 kcal","source":"HomeDish test kitchen"},
    {"name":"Chicken shawarma plate","emoji":"🧆","description":"Spiced chicken, crunchy salad, and cool yogurt sauce","tags":["35 min","family favorite"],"cuisine":"Middle Eastern","diet":"High protein","image":"https://images.unsplash.com/photo-1547058881-aa0edd92aab3?auto=format&fit=crop&w=900&q=85","ingredients":["300 g chicken thighs","shawarma spices","pita","tomato","cucumber","yogurt"],"steps":["Coat chicken with spices and roast until caramelized.","Stir lemon and garlic into yogurt.","Slice chicken and build the plate."],"nutrition":"450–570 kcal","source":"HomeDish test kitchen"},
    {"name":"Black bean street tacos","emoji":"🌮","description":"Smoky beans, lime slaw, and a quick weeknight dinner","tags":["20 min","budget"],"cuisine":"Mexican","diet":"Vegan","image":"https://images.unsplash.com/photo-1552332386-f8dd00dc2f85?auto=format&fit=crop&w=900&q=85","ingredients":["black beans","corn tortillas","cabbage","lime","avocado","smoked paprika"],"steps":["Warm beans with paprika and cumin.","Toss cabbage with lime.","Fill tortillas and finish with avocado."],"nutrition":"330–420 kcal","source":"HomeDish test kitchen"},
    {"name":"Ginger miso salmon","emoji":"🍣","description":"A five-ingredient glaze with a deeply savory finish","tags":["25 min","high protein"],"cuisine":"Japanese","diet":"High protein","image":"https://images.unsplash.com/photo-1485921325833-c519f76c4927?auto=format&fit=crop&w=900&q=85","ingredients":["2 salmon fillets","white miso","ginger","broccoli","brown rice"],"steps":["Whisk miso, ginger, and a little water.","Brush salmon and roast until flaky.","Serve with steamed broccoli and rice."],"nutrition":"460–550 kcal","source":"HomeDish test kitchen"},
    {"name":"Bibimbap-inspired bowl","emoji":"🥕","description":"Colorful vegetables, rice, and a punchy gochujang sauce","tags":["30 min","vegetarian"],"cuisine":"Korean","diet":"Vegetarian","image":"https://images.unsplash.com/photo-1553163147-622ab57be1c7?auto=format&fit=crop&w=900&q=85","ingredients":["brown rice","spinach","carrot","mushrooms","egg","gochujang"],"steps":["Cook rice and sauté each vegetable briefly.","Fry the egg until the edges crisp.","Build the bowl and drizzle with gochujang."],"nutrition":"420–510 kcal","source":"HomeDish test kitchen"},
    {"name":"Tomato white bean orzo","emoji":"🍅","description":"One-pan orzo with beans, greens, and parmesan","tags":["30 min","one pan"],"cuisine":"Italian","diet":"Vegetarian","image":"https://images.unsplash.com/photo-1473093295043-cdd812d0e601?auto=format&fit=crop&w=900&q=85","ingredients":["orzo","cannellini beans","tomatoes","spinach","parmesan","vegetable stock"],"steps":["Toast orzo with garlic and tomato.","Add stock and simmer until tender.","Fold in beans, spinach, and parmesan."],"nutrition":"390–480 kcal","source":"HomeDish test kitchen"},
    {"name":"Mushroom ramen","emoji":"🍜","description":"A deeply savory bowl with a lighter broth and extra greens","tags":["25 min","plant-based"],"cuisine":"Japanese","diet":"Vegan","image":"https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=900&q=85","ingredients":["ramen noodles","shiitake mushrooms","miso","bok choy","scallions","sesame"],"steps":["Brown mushrooms until deeply golden.","Build broth with miso and ginger.","Add noodles and greens; finish with scallions."],"nutrition":"350–440 kcal","source":"HomeDish test kitchen"},
]

def load_source_recipes():
    path=Path("data/recipe_library.json")
    if not path.exists(): return []
    try: raw=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError): return []
    hidden_names={"mapo tofu","coconut chickpea curry","jollof rice"}
    recipes=[]
    for index,item in enumerate(raw):
        source_name=str(item.get("name","Recipe")).strip().casefold()
        if any(hidden in source_name for hidden in hidden_names): continue
        image=item.get("image","")
        if isinstance(image,dict): image=image.get("url","")
        slug=re.sub(r"[^a-z0-9]+","-",str(item.get("name","recipe")).casefold()).strip("-") or "recipe"
        recipes.append({"id":str(item.get("id") or f"source:{index}:{slug}"),"name":item.get("name","Recipe"),"emoji":"🍽️","description":item.get("description","")[:180] or "A source-linked recipe to explore.","tags":[item.get("source","Web recipe"),"open source recipe"],"cuisine":item.get("cuisine","") or "Global","diet":"Flexible","image":image,"ingredients":item.get("ingredients",[]) if isinstance(item.get("ingredients",[]),list) else [],"steps":[],"nutrition":"","source":item.get("source","Recipe source"),"url":item.get("url","")})
    return recipes

def add_recipe_ids(recipes):
    for index,recipe in enumerate(recipes):
        if not recipe.get("id"):
            slug=re.sub(r"[^a-z0-9]+","-",str(recipe.get("name","recipe")).casefold()).strip("-") or "recipe"
            recipe["id"]=f"homedish:{index}:{slug}"
    return recipes

LIBRARY=add_recipe_ids(RECIPES+load_source_recipes())
WINE_CATALOG=load_wine_catalog()
NAV_PAGES=["Home","Discover","Photo check","Meal planner","Cook mode","Pantry","Grocery list","Recipe box"]
def init_state():
    for key,value in {"page":"Home","nav_page":"Home","nav_target":None,"planned":{"Mon":"Harissa salmon couscous","Wed":"Green shakshuka","Fri":"Dal with roasted cauliflower"},"pantry":["olive oil","garlic","rice","soy sauce"],"selected_recipe":None,"cooked_steps":[],"testimonial_index":0}.items(): st.session_state.setdefault(key,value)
    hidden_names={"mapo tofu","coconut chickpea curry","jollof rice"}
    replacement_cycle=iter(["Harissa salmon couscous","Green shakshuka","Dal with roasted cauliflower"])
    for day,meal in list(st.session_state.planned.items()):
        meal_name=str(meal).strip().casefold()
        if any(hidden in meal_name for hidden in hidden_names): st.session_state.planned[day]=next(replacement_cycle,"Harissa salmon couscous")
init_state()
if st.session_state.nav_target in NAV_PAGES:
    st.session_state.page=st.session_state.nav_target
    st.session_state.nav_page=st.session_state.nav_target
    st.session_state.nav_target=None
requested_page=st.query_params.get("page")
if requested_page in NAV_PAGES:
    st.session_state.page=requested_page
    st.session_state.nav_page=requested_page
    st.query_params.clear()

def navigate(target):
    st.session_state.page=target
    st.session_state.nav_target=target
    st.query_params.clear()
    st.rerun()

with st.container():
    st.markdown('<div class="topbar-anchor"></div>',unsafe_allow_html=True)
    top_logo,top_kitchen,top_discover,top_planner,top_cook,top_more,top_preferences=st.columns([1.25,1.55,1.15,1.35,1.1,.9,1.1])
    with top_logo:
        if st.button("home dish",key="top_home"): navigate("Home")
    with top_kitchen:
        if st.button("For your kitchen",key="top_kitchen"): navigate("Photo check")
    with top_discover:
        if st.button("Discover",key="top_discover"): navigate("Discover")
    with top_planner:
        if st.button("Meal planner",key="top_planner"): navigate("Meal planner")
    with top_cook:
        if st.button("Cook mode",key="top_cook"): navigate("Cook mode")
    with top_more:
        with st.popover("More"):
            if st.button("Pantry",key="top_pantry"): navigate("Pantry")
            if st.button("Grocery list",key="top_grocery"): navigate("Grocery list")
            if st.button("Recipe box",key="top_recipe_box"): navigate("Recipe box")
    with top_preferences:
        with st.popover("Preferences"):
            goal=st.selectbox("Main goal",["fewer calories","less sodium","more protein","less saturated fat"],key="top_goal")
            constraints=st.text_input("Diet or allergies",placeholder="e.g. vegetarian, peanut allergy",key="top_constraints")
            st.caption("Estimates, not medical advice. USDA-grounded ranges keep you in control.")

def recipe_card(recipe,key):
    if recipe.get("image"): st.image(recipe["image"],use_container_width=True)
    source_line=f'<div style="color:#db654c;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">{recipe.get("source", "HomeDish kitchen")}</div>'
    st.markdown(f'<div class="recipe-card">{source_line}<div class="recipe-emoji">{recipe["emoji"]}</div><h3>{recipe["name"]}</h3><p>{recipe["description"]}</p>{" ".join(f"<span class=\'tag\'>{tag}</span>" for tag in recipe["tags"])}</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    if c1.button("Plan it",key=key): st.session_state.planned["Tue"]=recipe["name"]; st.toast(f'{recipe["name"]} added to Tuesday')
    if c2.button("Cook",key=f"cook_{key}"):
        st.session_state.selected_recipe=recipe["name"]
        navigate("Cook mode")

def render_catalog(recipes, prefix):
    page_size=12
    page_count=max(1,(len(recipes)+page_size-1)//page_size)
    control_left,control_right=st.columns([3,1])
    state_key=f"{prefix}_page"
    if st.session_state.get(state_key,1)>page_count: st.session_state[state_key]=1
    with control_right: catalog_page=st.number_input("Page",min_value=1,max_value=page_count,value=st.session_state.get(state_key,1),step=1,key=state_key)
    start=(catalog_page-1)*page_size
    for row_start in range(start,min(start+page_size,len(recipes)),3):
        cols=st.columns(3)
        for col,recipe,idx in zip(cols,recipes[row_start:row_start+3],range(row_start,row_start+3)):
            with col: recipe_card(recipe,f"{prefix}_{idx}")
    if page_count>1: st.caption(f"Showing {start+1}–{min(start+page_size,len(recipes))} of {len(recipes)} recipes")

def ingredient_editor(estimates):
    edited=[]
    # Keep the visual marker and live Streamlit controls in one parent block.
    # The stylesheet scopes the dark treatment to this block only.
    with st.container():
        st.markdown('<div class="ingredient-scope"><div class="ingredient-stage"><div class="ingredient-stage-title"><div><h3>What we found in your dish</h3><p>Check the model\'s estimate before we calculate.</p></div><span class="ingredient-mode">edit mode</span></div><div class="ingredient-head"><span>Ingredient</span><span>Low · g</span><span>High · g</span><span>Seen</span><span>Why / note</span></div></div></div>', unsafe_allow_html=True)
        for idx,item in enumerate(estimates):
            with st.container(border=True):
                cols=st.columns([3,1.1,1.1,.8,2])
                name=cols[0].text_input("Ingredient",value=item.name,key=f"ingredient_name_{idx}",label_visibility="collapsed")
                low=cols[1].number_input("Low grams",min_value=0.0,value=float(item.grams_low),step=1.0,key=f"ingredient_low_{idx}",label_visibility="collapsed")
                high=cols[2].number_input("High grams",min_value=0.0,value=float(item.grams_high),step=1.0,key=f"ingredient_high_{idx}",label_visibility="collapsed")
                visible=cols[3].checkbox("Visible",value=item.visible,key=f"ingredient_visible_{idx}",label_visibility="collapsed")
                reason=cols[4].text_input("Reason",value=item.reason or "",key=f"ingredient_reason_{idx}",label_visibility="collapsed",placeholder="optional note")
                edited.append({"name":name,"grams_low":low,"grams_high":high,"visible":visible,"reason":reason or None})
    return edited

def render_recommendation(version, check, index):
    status = "A good fit for your goal" if check.accepted else "Needs a quick safety review"
    st.markdown(f'<div class="recommendation-card"><div class="recommendation-kicker">{["Gentle","Balanced"][min(index,1)]} change · {status}</div><h3>{version.title}</h3><p><b>{version.authenticity_note}</b><br>{version.flavor_tradeoff}</p></div>', unsafe_allow_html=True)
    if version.changes:
        st.markdown("**What changes**")
        for change in version.changes:
            if change.to == "updated amount" and change.why == "Supports the selected goal.":
                st.markdown(f'<div class="recommendation-change">✦ {change.from_}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="recommendation-change"><strong>{change.from_}</strong> → {change.to}<small>{change.why}</small></div>', unsafe_allow_html=True)
    if version.steps:
        st.markdown("**How to make it**")
        st.markdown("".join(f'<div class="step-row"><span class="step-number">{step_index}</span><span>{step}</span></div>' for step_index,step in enumerate(version.steps,1)), unsafe_allow_html=True)
    if version.new_ingredients:
        chips="".join(f'<span class="ingredient-chip">{ingredient.name}</span>' for ingredient in version.new_ingredients)
        st.markdown(f"**For the lighter version**<br>{chips}", unsafe_allow_html=True)

def render_recipe_recommendation(recommendation, recipe, key):
    image=recipe.get("image")
    if image:
        st.image(image,use_container_width=True)
    name=html.escape(str(recipe.get("name","Recipe")))
    source=html.escape(str(recipe.get("source","Recipe library")))
    cuisine=html.escape(str(recipe.get("cuisine","Global")))
    diet=html.escape(str(recipe.get("diet","Flexible")))
    reason=html.escape(recommendation.reason)
    health=html.escape(recommendation.health_angle)
    interest=html.escape(recommendation.interest_angle)
    chips="".join(f'<span class="how-about-chip">{html.escape(str(item))}</span>' for item in recommendation.shared_ingredients)
    shared_markup=chips or '<span class="how-about-chip">ingredient overlap verified</span>'
    st.markdown(f'<div class="how-about-card"><div class="how-about-body"><div class="how-about-source">{source} · {cuisine} · {diet}</div><h3>{name}</h3><p>{reason}</p><div class="how-about-label">Shared ingredients</div><div>{shared_markup}</div><div class="how-about-label">Why it fits</div><div class="how-about-angle">{health}<br><br>{interest}</div></div></div>',unsafe_allow_html=True)
    if recipe.get("url"):
        st.link_button("Open recipe source ↗",recipe["url"],use_container_width=True)
    if st.button("Plan it",key=f"how_about_plan_{key}",use_container_width=True):
        st.session_state.planned["Tue"]=recipe["name"]
        st.toast(f'{recipe["name"]} added to Tuesday')

def render_wine_pairing(explanation, wine, key):
    name=html.escape(str(wine.get("name","Wine")))
    wine_type=html.escape(str(wine.get("type","Wine")))
    grapes=html.escape(", ".join(str(grape) for grape in wine.get("grapes",[])[:3]) or "grape not listed")
    body=html.escape(str(wine.get("body","Body not listed")))
    acidity=html.escape(str(wine.get("acidity","Acidity not listed")))
    region=html.escape(" · ".join(str(item) for item in [wine.get("region"),wine.get("country")] if item))
    matched="".join(f'<span class="wine-chip">{html.escape(str(item))}</span>' for item in wine.get("matched_pairings",[]))
    rating=float(wine.get("rating") or 0)
    rating_text=f"★ {rating:.2f} · {int(wine.get('rating_count') or 0)} ratings" if rating else "Rating not available in this catalog sample"
    st.markdown(f'<div class="wine-card"><div class="wine-card-meta">{wine_type} · {body} · {acidity}</div><h3>{name}</h3><p>{grapes}{f"<br>{region}" if region else ""}</p><div class="wine-rating">{rating_text}</div><div class="how-about-label" style="color:#f0d29d">Listed food matches</div><div>{matched or "<span class=\"wine-chip\">style match</span>"}</div><div class="wine-why">{html.escape(explanation.explanation)}</div></div>',unsafe_allow_html=True)
    link=wine.get("website") or wine.get("source_url")
    if link:
        st.link_button("Open winery / source ↗",link,use_container_width=True)

def planner_strip():
    cols=st.columns(7)
    for col,(day,date) in zip(cols,[("Mon","14"),("Tue","15"),("Wed","16"),("Thu","17"),("Fri","18"),("Sat","19"),("Sun","20")]):
        meal=st.session_state.planned.get(day)
        with col: st.markdown(f'<div class="planner-day {"active" if day=="Tue" else ""}"><div class="day-name">{day}</div><div class="day-date">{date}</div>{f"<div class=\"meal-pill green\">{meal}</div>" if meal else "<div style=\"color:#a8b0aa;font-size:11px;margin-top:28px\">+ Add meal</div>"}</div>',unsafe_allow_html=True)

page=st.session_state.page
if page=="Home":
    st.markdown("""
    <div class="landing-page">
      <section class="landing-hero">
        <div class="landing-hero-copy">
          <div class="landing-eyebrow">A smarter way to eat what feels like home</div>
          <h1>Make room for <em>more</em> of what you love.</h1>
          <p>HomeDish sees the whole plate, respects the recipe, and finds lighter ways to keep the flavor, memory, and culture intact.</p>
          <div class="landing-hero-meta"><span class="landing-dot"></span><span>238 recipes · 14 cuisines · your kitchen, your call</span></div>
        </div>
        <div class="landing-hero-visual">
          <div class="landing-plate-image"></div>
          <div class="landing-float top"><div class="landing-float-kicker">Tonight's plate</div><div class="landing-float-title">+ balance</div><div class="landing-float-copy">A little more greens. The same family recipe.</div></div>
          <div class="landing-float main"><div class="landing-float-kicker">Photo check complete</div><div class="landing-float-title">Harissa salmon couscous</div><div class="landing-float-copy">A bright, protein-rich plate with herbs, citrus, and a lighter finish.</div><div class="landing-meter"><i></i></div><div class="landing-float-stats"><span>confidence</span><span>92%</span></div></div>
        </div>
      </section>
    </div>
    """,unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="landing-actions-anchor"></div>',unsafe_allow_html=True)
        action_one,action_two=st.columns([1,1])
        with action_one:
            if st.button("Start with a photo →",key="landing_photo_cta",use_container_width=True): navigate("Photo check")
        with action_two:
            if st.button("Explore the recipe library ↗",key="landing_library_cta",use_container_width=True): navigate("Discover")

    st.markdown('<div class="landing-marquee"><span><strong>HOME DISH</strong> · food, but make it personal</span><span><b>●</b> 7-day planning</span><span><b>●</b> USDA-grounded estimates</span><span><b>●</b> culture-first swaps</span></div>',unsafe_allow_html=True)
    st.markdown('<div id="landing-features" class="landing-section"><div class="landing-section-head"><div><div class="landing-kicker">One plate. Three possibilities.</div><h2>Small decisions can change the whole way dinner feels.</h2></div><p>You stay in control of the ingredient list. HomeDish simply helps you see the options, then make a choice that fits your body and your table.</p></div></div>',unsafe_allow_html=True)
    feature_cols=st.columns(3,gap="large")
    feature_cards=[
        ('01','See what is really there','Snap a photo and get a transparent ingredient estimate—including the oils, sauces, and toppings that are easy to miss.','aqua','✦'),
        ('02','Keep the soul of it','Swap one decision at a time: less sodium, more protein, a gentler cooking method. The dish should still taste like yours.','lilac','↗'),
        ('03','Feel lighter, stay connected','Plan around the cuisines you grew up with, from Japanese soba to Sunday shawarma and everything in between.','lime','03'),
    ]
    for col,(number,title,copy,color,art) in zip(feature_cols,feature_cards):
        with col: st.markdown(f'<div class="landing-feature {color}"><small>{number}</small><div class="landing-feature-art">{art}</div><h3>{title}</h3><p>{copy}</p></div>',unsafe_allow_html=True)

    testimonials=[
        ('“I wanted to lose weight without turning my family recipes into diet food. HomeDish helped me keep the Sunday rice dishes, just with a little more balance. I feel lighter after dinner—and still fully at home.”','Amina K.','Illustrative member story · Lagos / London'),
        ('“The best part is seeing the swap before I cook. I can keep the ginger, scallions, and heat I love, then choose a lighter base that works for my week.”','Daniel R.','Illustrative member story · Singapore'),
        ('“My grandmother’s tofu recipe finally feels like something I can make regularly. The app explains the tradeoff instead of making me feel guilty about the original.”','Mei L.','Illustrative member story · Chengdu / New York'),
        ('“I stopped asking whether a food was ‘good’ or ‘bad.’ I ask what would make this plate work better for me today. That shift has made healthy eating feel possible.”','Sofia M.','Illustrative member story · Mexico City'),
        ('“Planning used to erase the variety from my week. Now I can build a lighter meal plan around the dishes I actually crave.”','Noah B.','Illustrative member story · Accra / Toronto'),
    ]
    with st.container():
        st.markdown('<div id="landing-stories" class="landing-stories-scope"><div class="landing-stories-head"><div class="landing-kicker">What our table says</div><h2>Healthy can still sound like home.</h2></div></div>',unsafe_allow_html=True)
        nav_left,nav_label,nav_right=st.columns([1,5,1])
        with nav_left:
            if st.button("←",key="story_prev",use_container_width=True): st.session_state.testimonial_index=(st.session_state.testimonial_index-1)%len(testimonials); st.rerun()
        with nav_label: st.markdown('<div class="landing-story-nav"><span class="landing-story-nav-label">member notes</span></div>',unsafe_allow_html=True)
        with nav_right:
            if st.button("→",key="story_next",use_container_width=True): st.session_state.testimonial_index=(st.session_state.testimonial_index+1)%len(testimonials); st.rerun()
        story_index=st.session_state.testimonial_index
        story_cols=st.columns(3,gap="large")
        for col,review in zip(story_cols,[testimonials[(story_index+i)%len(testimonials)] for i in range(3)]):
            with col: st.markdown(f'<div class="landing-story-card"><p>{review[0]}</p><footer>{review[1]}<span>{review[2]}</span></footer></div>',unsafe_allow_html=True)
        st.markdown('<div class="landing-story-note">Stories above are illustrative product examples, not verified medical or weight-loss outcomes.</div>',unsafe_allow_html=True)

    st.markdown('<div class="landing-culture"><div><div class="landing-kicker">Culture is the ingredient</div><h2>Feel lighter without leaving your table.</h2><p>From the wok to the tiffin, from a Sunday stew to a ten-minute bowl, your food carries more than nutrition. It carries people. HomeDish helps you care for both.</p></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="landing-bottom-cta"><div class="landing-kicker">Your next meal is already waiting</div><h2>Bring us the dish you love.</h2><p>Start with a photo, browse the library, or build a week around the flavors that make you feel most like yourself.</p></div>',unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="landing-actions-anchor"></div>',unsafe_allow_html=True)
        final_one,final_two=st.columns([1,1])
        with final_one:
            if st.button("Check my plate →",key="landing_bottom_photo",use_container_width=True): navigate("Photo check")
        with final_two:
            if st.button("See all recipes ↗",key="landing_bottom_library",use_container_width=True): navigate("Discover")
elif page=="Discover":
    st.markdown('<div class="eyebrow">Eat curiously</div><h1>Discover your next favorite</h1><p style="color:#718079">Recipes with a point of view—organized around flavor, culture, and the way you actually cook.</p>',unsafe_allow_html=True)
    f1,f2,f3=st.columns([1,1,1]); search=f1.text_input("Search",placeholder="tofu, curry, rice…",label_visibility="collapsed"); cuisine_filter=f2.selectbox("Cuisine",["All cuisines","Chinese","South Asian","West African","Korean","Caribbean","Mediterranean","Thai","Japanese","Middle Eastern","Mexican","Italian"],label_visibility="collapsed"); diet_filter=f3.selectbox("Fits your kitchen",["All diets","Vegan","Vegetarian","High protein","Budget"],label_visibility="collapsed")
    filtered=[r for r in LIBRARY if (not search or search.lower() in (r["name"]+r["description"]).lower()) and (cuisine_filter=="All cuisines" or r["cuisine"]==cuisine_filter) and (diet_filter=="All diets" or diet_filter in r["diet"])]
    st.markdown(f'<div class="section-label"><h2>{len(filtered)} recipes for you</h2><span>freshly curated</span></div>',unsafe_allow_html=True)
    render_catalog(filtered,"discover")
elif page=="Meal planner":
    st.markdown('<div class="eyebrow">Plan with intention</div><h1>Meal planner</h1><p style="color:#718079">A flexible week, built around dishes you actually want to eat.</p>',unsafe_allow_html=True); st.markdown('<div class="section-label"><h2>March 14–20</h2><span>+ Add a meal</span></div>',unsafe_allow_html=True); planner_strip()
    st.markdown('<div class="section-label"><h2>Pick something to add</h2><span>from your recipe box</span></div>',unsafe_allow_html=True)
    cols=st.columns(3)
    for col,recipe,idx in zip(cols,RECIPES,range(len(RECIPES))):
        with col: recipe_card(recipe,f"planner_{idx}")
elif page=="Cook mode":
    recipe=next((r for r in LIBRARY if r["name"]==st.session_state.selected_recipe),RECIPES[0])
    st.markdown('<div class="eyebrow">Hands-on cooking</div>',unsafe_allow_html=True)
    col1,col2=st.columns([1.05,1.2],gap="large")
    with col1: st.image(recipe["image"],use_container_width=True); st.markdown(f'<span class="tag">{recipe["cuisine"]}</span> <span class="tag">{recipe["diet"]}</span><h1>{recipe["name"]}</h1><p style="color:#718079">{recipe["description"]}</p>',unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="section-label"><h2>Ingredients</h2><span>serves 2</span></div>',unsafe_allow_html=True)
        for ingredient in recipe["ingredients"]: st.checkbox(ingredient,key=f"ingredient_{recipe['name']}_{ingredient}")
        st.markdown('<div class="section-label"><h2>Method</h2><span>cook at your pace</span></div>',unsafe_allow_html=True)
        for idx,step in enumerate(recipe["steps"],1):
            done=st.checkbox(f"{idx:02d}  {step}",key=f"step_{recipe['name']}_{idx}")
            if done and idx not in st.session_state.cooked_steps: st.session_state.cooked_steps.append(idx)
        st.progress(len(st.session_state.cooked_steps)/max(1,len(recipe["steps"])),text=f"{len(st.session_state.cooked_steps)} of {len(recipe['steps'])} steps complete")
        if not recipe["steps"] and recipe.get("url"): st.link_button("Open full recipe source ↗",recipe["url"],use_container_width=True)
        st.markdown(f'<div class="tip"><b>Estimated nutrition</b><br>{recipe["nutrition"]} per serving · ranges are estimates, not medical advice.</div>',unsafe_allow_html=True)
elif page=="Pantry":
    st.markdown('<div class="eyebrow">What you already have</div><h1>Pantry</h1><p style="color:#718079">Keep your staples here so meal ideas use what is already in your kitchen.</p>',unsafe_allow_html=True)
    with st.form("add_pantry"):
        item=st.text_input("Add an ingredient",placeholder="e.g. canned tomatoes"); submitted=st.form_submit_button("Add to pantry")
        if submitted and item: st.session_state.pantry.append(item.strip()); st.toast(f"Added {item.strip()}")
    st.markdown('<div class="section-label"><h2>Your staples</h2><span>used in recommendations</span></div>',unsafe_allow_html=True)
    cols=st.columns(3)
    for idx,item in enumerate(st.session_state.pantry):
        with cols[idx%3]:
            st.markdown(f'<div class="recipe-card" style="min-height:70px"><span class="tag">IN PANTRY</span><h3 style="margin-top:10px">{item}</h3></div>',unsafe_allow_html=True)
    st.markdown('<div class="section-label"><h2>Use these tonight</h2></div>',unsafe_allow_html=True)
    st.info("You have ingredients for a quick tofu bowl, green shakshuka, or fried rice. Add fresh produce from the grocery list.")
elif page=="Recipe box":
    st.markdown('<div class="eyebrow">Your collection</div><h1>Recipe box</h1><p style="color:#718079">Save the meals that feel like home, then make them work for this week.</p>',unsafe_allow_html=True)
    search=st.text_input("Search recipes",placeholder="Try tofu, curry, one pan…",label_visibility="collapsed"); filtered=[r for r in LIBRARY if not search or search.lower() in (r["name"]+r["description"]+" ".join(r["tags"])).lower()]
    render_catalog(filtered,"box")
elif page=="Grocery list":
    st.markdown('<div class="eyebrow">Shop with a plan</div><h1>Grocery list</h1><p style="color:#718079">Everything for this week, grouped so the store run feels simple.</p>',unsafe_allow_html=True)
    grocery={"Produce":["scallions","garlic","ginger","cilantro","bell peppers"],"Protein":["firm tofu","chicken breast"],"Pantry & sauces":["doubanjiang","soy sauce","vegetable stock","rice"],"Already have":st.session_state.pantry}
    st.markdown(f'<div class="tip"><b>{sum(len(v) for v in grocery.values())} items</b> · 3 meals · pantry staples excluded from the shop</div>',unsafe_allow_html=True)
    for section,items in grocery.items():
        st.markdown(f'<div class="section-label"><h2>{section}</h2></div>',unsafe_allow_html=True); cols=st.columns(2)
        for idx,item in enumerate(items): cols[idx%2].checkbox(item,key=f"shop_{section}_{idx}")
    st.download_button("Download list","\n".join(f"{k}:\n"+"\n".join(f"- {x}" for x in v) for k,v in grocery.items()),"homedish-grocery-list.txt",use_container_width=True)
else:
    st.markdown('<div class="eyebrow">The smart part</div><h1>Check a dish</h1><p style="color:#718079">Upload a photo, then stay in control of every estimate.</p>',unsafe_allow_html=True)
    file=st.file_uploader("Drop a dish photo here",type=["jpg","jpeg","png"],label_visibility="collapsed"); hint=st.text_input("Dish hint",placeholder="Optional — e.g. harissa salmon couscous"); cuisine=st.text_input("Cuisine hint",placeholder="Optional — e.g. Mediterranean")
    if file and st.button("Recognize my dish",use_container_width=True):
        path=Path(".homedish_upload.jpg"); path.write_bytes(file.getvalue())
        try:
            st.session_state.recognition=Recognition.model_validate(recognize_with_backend(path,hint,cuisine)); st.session_state.path=str(path)
        except Exception as e: st.error(f"Could not analyze this image: {e}. Is the vision backend running on port 8000?")
    if "recognition" in st.session_state:
        r=st.session_state.recognition
        if not r.is_food: st.warning("This doesn't look like food. Please upload a dish photo."); st.stop()
        st.markdown(f'<div class="section-label"><h2>We see: {r.dish_name}</h2><span>{int(r.confidence*100)}% confidence</span></div>',unsafe_allow_html=True)
        all_estimates=r.ingredients+r.hidden_ingredients
        st.markdown('<div class="ingredient-note"><b>Your edit is the accuracy lever.</b> Hidden oils and sauces are estimates. Adjust the grams until the rows look like your kitchen.</div>',unsafe_allow_html=True)
        edited=ingredient_editor(all_estimates)
        st.markdown('<div class="tip">Every gram stays editable. Items we could not match to USDA will be clearly marked rather than silently counted.</div>',unsafe_allow_html=True)
        if st.button("Calculate nutrition & swaps →",use_container_width=True):
            try:
                b=Budget(); items=[IngredientEstimate.model_validate(x) for x in edited] if edited and all_estimates else []; ms=match(items,b); matched_ingredients=[m.model_dump() for m in ms]; counted=[m for m in matched_ingredients if m.get("fdc_id")]; n=calculate_with_backend(counted,r.servings_estimate); s=suggest(r.dish_name,r.cuisine,matched_ingredients,n,goal,constraints,b); checks=[critic(v,constraints) for v in s.versions[:2]]; recipe_recommendations=recommend_recipes(LIBRARY,matched_ingredients,r.dish_name,r.cuisine,goal,constraints,b); wine_profile=profile_dish(r.dish_name,r.cuisine,matched_ingredients,n); wine_candidates=rank_wines(WINE_CATALOG,wine_profile,limit=3); wine_pairings=explain_pairings(wine_profile,wine_candidates,b); st.session_state.result=(ms,n,s,checks,recipe_recommendations,wine_profile,wine_candidates,wine_pairings,b)
            except Exception as e: st.error(f"Calculation failed: {e}")
    if "result" in st.session_state:
        result_data=st.session_state.result
        if len(result_data)==5:
            ms,n,s,checks,b=result_data; recipe_recommendations=[]; wine_profile=None; wine_candidates=[]; wine_pairings=[]
        elif len(result_data)==6:
            ms,n,s,checks,recipe_recommendations,b=result_data; wine_profile=None; wine_candidates=[]; wine_pairings=[]
        else:
            ms,n,s,checks,recipe_recommendations,wine_profile,wine_candidates,wine_pairings,b=result_data
        visible_versions=s.versions[:2]
        st.markdown('<div class="section-label"><h2>Ways to lighten it</h2><span>gentle → balanced</span></div>',unsafe_allow_html=True); tabs=st.tabs([v.title for v in visible_versions])
        for index,(tab,v,c) in enumerate(zip(tabs,visible_versions,checks)):
            with tab:
                render_recommendation(v,c,index)
                if c.accepted and st.button("Add ingredients to grocery list",key=f"swap_grocery_{index}"): st.session_state.grocery=build([x.model_dump() for x in v.new_ingredients],r.servings_estimate); st.toast("Added to grocery list")
        st.markdown('<div class="section-label"><h2>How about?</h2><span>same ingredients · new direction</span></div>',unsafe_allow_html=True)
        st.caption("Three recipes from your kitchen's ingredient orbit, selected from the HomeDish library and reranked by the ingredient-matching agent.")
        if recipe_recommendations:
            recipe_by_id={str(recipe.get("id")):recipe for recipe in LIBRARY}
            recommendation_cols=st.columns(3,gap="large")
            for col,recommendation in zip(recommendation_cols,recipe_recommendations[:3]):
                recipe=recipe_by_id.get(recommendation.recipe_id)
                if recipe:
                    with col: render_recipe_recommendation(recommendation,recipe,recommendation.recipe_id.replace(":","_"))
        else:
            st.info("We could not find three linkable recipes with enough ingredient overlap for this dish yet. Try confirming a few more ingredient names above.")
        st.markdown('<div class="section-label"><h2>What wine do I pair it with?</h2><span>rules first · explanation second</span></div>',unsafe_allow_html=True)
        if wine_profile and wine_pairings:
            rationale=" · ".join(wine_profile.rationale[:2])
            tags="".join(f'<span class="wine-chip">{html.escape(str(tag))}</span>' for tag in wine_profile.pairing_tags)
            st.markdown(f'<div class="wine-style-card"><div class="wine-style-kicker">Dish profile → target style</div><h3>{html.escape(wine_profile.target_style)}</h3><p>{html.escape(rationale)}</p><div style="margin-top:10px">{tags}</div></div>',unsafe_allow_html=True)
            wine_by_id={str(wine.get("id")):wine for wine in wine_candidates}
            wine_cols=st.columns(3,gap="large")
            for col,explanation in zip(wine_cols,wine_pairings[:3]):
                wine=wine_by_id.get(explanation.wine_id)
                if wine:
                    with col: render_wine_pairing(explanation,wine,explanation.wine_id.replace(":","_"))
        elif WINE_CATALOG:
            st.info("Wine pairing will appear after the dish calculation is complete.")
        else:
            st.info("The wine catalog is not available yet. Run data/import_xwines.py to build it.")
        st.sidebar.metric("LLM calls",b.calls); st.sidebar.metric("Measured cost",f"${b.cost_usd:.4f}")
