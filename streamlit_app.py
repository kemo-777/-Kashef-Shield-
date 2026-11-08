import time
from datetime import datetime
import pandas as pd
import streamlit as st

from engine import (
    ProductionFeatureStore,
    GlobalConsortiumNetwork,
    VoicePhishingShield,
    CyberSecurityShield,
    compute_hardware_hash,
    initialize_models
)

st.set_page_config(
    page_title="Global Banking Fraud & Defense Core",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# قاموس اللغات الـ 20
LANGS = {
    "ar": {"dir": "rtl", "title": "🛡️ المنظومة العالمية لمكافحة الاحتيال المصرفي", "tab1": "💳 فحص المعاملات وبصمة العتاد", "tab2": "📞 درع رصد المكالمات الاحتيالية", "tab3": "🌍 التحالف المصرفي الدولي", "btn": "⚡ فحص فوري للمخاطر", "eval_call": "🔍 فحص المكالمة"},
    "en": {"dir": "ltr", "title": "🛡️ Global Banking Fraud & Defense Core", "tab1": "💳 Transaction & Hardware Audit", "tab2": "📞 Anti-Vishing Call Shield", "tab3": "🌍 Global Consortium Network", "btn": "⚡ Evaluate Transaction", "eval_call": "🔍 Inspect Call"},
    "es": {"dir": "ltr", "title": "🛡️ Núcleo Global Antifraude Bancario", "tab1": "💳 Auditoría de Transacciones", "tab2": "📞 Escudo de Llamadas", "tab3": "🌍 Red de Consorcio", "btn": "⚡ Evaluar Transacción", "eval_call": "🔍 Inspeccionar"},
    "zh": {"dir": "ltr", "title": "🛡️ 全球银行反欺诈核心", "tab1": "💳 交易与硬件审计", "tab2": "📞 语音防钓鱼", "tab3": "🌍 联盟网络", "btn": "⚡ 评估交易", "eval_call": "🔍 审查通话"},
    "fr": {"dir": "ltr", "title": "🛡️ Système Mondial Antifraude", "tab1": "💳 Audit des Transactions", "tab2": "📞 Bouclier Téléphonique", "tab3": "🌍 Réseau Consortium", "btn": "⚡ Évaluer", "eval_call": "🔍 Analyser"},
    "de": {"dir": "ltr", "title": "🛡️ Globales Betrugserkennungssystem", "tab1": "💳 Transaktionsprüfung", "tab2": "📞 Anruf-Schutzschild", "tab3": "🌍 Konsortium", "btn": "⚡ Bewerten", "eval_call": "🔍 Prüfen"},
    "hi": {"dir": "ltr", "title": "🛡️ धोखाधड़ी निवारण कोर", "tab1": "💳 लेनदेन लेखापरीक्षा", "tab2": "📞 कॉल शील्ड", "tab3": "🌍 कंसोर्टियम नेटवर्क", "btn": "⚡ मूल्यांकन करें", "eval_call": "🔍 जांच करें"},
    "ru": {"dir": "ltr", "title": "🛡️ Система Защиты от Мошенничества", "tab1": "💳 Аудит транзакций", "tab2": "📞 Защита звонков", "tab3": "🌍 Сеть Консорциума", "btn": "⚡ Оценить", "eval_call": "🔍 Проверить"},
    "ja": {"dir": "ltr", "title": "🛡️ 不正防止インテリジェンス", "tab1": "💳 取引監査", "tab2": "📞 通話シールド", "tab3": "🌍 コンソーシアム", "btn": "⚡ 評価する", "eval_call": "🔍 検査"},
    "pt": {"dir": "ltr", "title": "🛡️ Núcleo Antifraude Global", "tab1": "💳 Auditoria", "tab2": "📞 Proteção de Voz", "tab3": "🌍 Consórcio", "btn": "⚡ Avaliar", "eval_call": "🔍 Inspecionar"},
    "tr": {"dir": "ltr", "title": "🛡️ Sahtekarlık Tespit Sistemi", "tab1": "💳 İşlem Denetimi", "tab2": "📞 Çağrı Kalkanı", "tab3": "🌍 Konsorsiyum", "btn": "⚡ Değerlendir", "eval_call": "🔍 Denetle"},
    "it": {"dir": "ltr", "title": "🛡️ Sistema Antifrode Bancario", "tab1": "💳 Controllo Transazioni", "tab2": "📞 Scudo Vocale", "tab3": "🌍 Rete Consorzio", "btn": "⚡ Valuta", "eval_call": "🔍 Esamina"},
    "ko": {"dir": "ltr", "title": "🛡️ 금융 사기 탐지 코어", "tab1": "💳 거래 감사", "tab2": "📞 보이스피싱 쉴드", "tab3": "🌍 글로벌 네트워크", "btn": "⚡ 평가", "eval_call": "🔍 검사"},
    "id": {"dir": "ltr", "title": "🛡️ Pencegahan Penipuan Global", "tab1": "💳 Audit Transaksi", "tab2": "📞 Pelindung Panggilan", "tab3": "🌍 Jaringan", "btn": "⚡ Evaluasi", "eval_call": "🔍 Periksa"},
    "vi": {"dir": "ltr", "title": "🛡️ Phòng Chống Gian Lận", "tab1": "💳 Kiểm toán", "tab2": "📞 Khiên bảo vệ", "tab3": "🌍 Liên minh", "btn": "⚡ Đánh giá", "eval_call": "🔍 Kiểm tra"},
    "nl": {"dir": "ltr", "title": "🛡️ Fraudedetectiesysteem", "tab1": "💳 Transactie Audit", "tab2": "📞 Gesprekschild", "tab3": "🌍 Consortium", "btn": "⚡ Evalueer", "eval_call": "🔍 Inspecteer"},
    "fa": {"dir": "rtl", "title": "🛡️ سامانه ضد کلاهبرداری بانکی", "tab1": "💳 حسابرسی تراکنش‌ها", "tab2": "📞 سپر تماس صوتی", "tab3": "🌍 اتحادیه بانکی", "btn": "⚡ ارزیابی", "eval_call": "🔍 بررسی"},
    "pl": {"dir": "ltr", "title": "🛡️ Centrum Wykrywania Oszustw", "tab1": "💳 Audyt transakcji", "tab2": "📞 Tarcza połączeń", "tab3": "🌍 Sieć", "btn": "⚡ Oceń", "eval_call": "🔍 Sprawdź"},
    "uk": {"dir": "ltr", "title": "🛡️ Система Захисту від Шахрайства", "tab1": "💳 Аудит транзакцій", "tab2": "📞 Захист дзвінків", "tab3": "🌍 Мережа", "btn": "⚡ Оцінити", "eval_call": "🔍 Перевірити"},
    "sv": {"dir": "ltr", "title": "🛡️ Bankbedrägerisystem", "tab1": "💳 Transaktionsgranskning", "tab2": "📞 Samtalsskydd", "tab3": "🌍 Konsortium", "btn": "⚡ Utvärdera", "eval_call": "🔍 Inspektera"}
}

# القائمة الجانبية لإعدادات المظهر واللغة
with st.sidebar:
    st.subheader("⚙️ System Preferences")
    lang_key = st.selectbox("Language / اللغة:", list(LANGS.keys()), index=0)
    theme_choice = st.radio("Theme / المظهر:", ["Neon ⚡", "Dark 🌙", "Light ☀️"], index=0)

cfg = LANGS[lang_key]
is_rtl = (cfg["dir"] == "rtl")

# تحديد ألوان الثيمات
if theme_choice == "Neon ⚡":
    bg_app = "#030712"
    txt_color = "#00f2fe"
    card_bg = "#080f24"
    border_col = "#00f2fe"
    shadow_css = "0 0 16px rgba(0, 242, 254, 0.35)"
    metric_val = "#38bdf8"
elif theme_choice == "Light ☀️":
    bg_app = "#f8fafc"
    txt_color = "#0f172a"
    card_bg = "#ffffff"
    border_col = "#cbd5e1"
    shadow_css = "0 2px 4px rgba(0,0,0,0.06)"
    metric_val = "#0284c7"
else:  # Dark
    bg_app = "#0b0f19"
    txt_color = "#f8fafc"
    card_bg = "#111827"
    border_col = "#1f2937"
    shadow_css = "none"
    metric_val = "#38bdf8"

# حقن التنسيق لضمان ثبات الواجهة وتطبيق الثيم ومنع ظهور أكواد نصية
css_style = f"""
<style>
* {{
    box-sizing: border-box !important;
}}
html, body, [data-testid="stAppViewContainer"], .stApp {{
    background-color: {bg_app} !important;
    color: {txt_color} !important;
    direction: {cfg["dir"]} !important;
    text-align: {"right" if is_rtl else "left"} !important;
    overflow-x: hidden !important;
}}
[data-testid="stSidebar"], section[data-testid="stSidebar"] {{
    background-color: {card_bg} !important;
    border-{"left" if is_rtl else "right"}: 1px solid {border_col} !important;
}}
div[data-testid="stMetric"], div[data-testid="stForm"], .stDataFrame {{
    background-color: {card_bg} !important;
    color: {txt_color} !important;
    border: 1px solid {border_col} !important;
    border-radius: 12px !important;
    box-shadow: {shadow_css} !important;
}}
div[data-testid="stMetricValue"] {{
    color: {metric_val} !important;
}}
h1, h2, h3, p, span, label {{
    color: {txt_color} !important;
}}
button[kind="primaryFormSubmit"], .stButton > button {{
    width: 100% !important;
    min-height: 48px !important;
    font-size: 16px !important;
    font-weight: bold !important;
    border-radius: 8px !important;
}}
@media screen and (max-width: 768px) {{
    .stApp {{
        padding: 8px !important;
    }}
    div[data-testid="column"] {{
        width: 100% !important;
        flex: 1 1 100% !important;
    }}
}}
</style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# إدارة الحالة في الذاكرة
if "app_engine" not in st.session_state:
    iso, calib, features = initialize_models()
    st.session_state.app_engine = {
        "anomaly": iso,
        "classifier": calib,
        "features": features,
        "store": ProductionFeatureStore(),
        "consortium": GlobalConsortiumNetwork(),
        "voice": VoicePhishingShield(),
        "security": CyberSecurityShield(max_reqs=120)
    }

if "tx_records" not in st.session_state: st.session_state.tx_records = []
if "call_records" not in st.session_state: st.session_state.call_records = []

eng = st.session_state.app_engine

st.title(cfg["title"])

# بطاقات الإحصائيات
tx_data = st.session_state.tx_records
m1, m2, m3, m4 = st.columns(4)
m1.metric("إجمالي العمليات", len(tx_data))
m2.metric("المقبولة ✅", sum(1 for x in tx_data if x["Decision"] == "APPROVE"))
m3.metric("مراجعة (OTP) ⚠️", sum(1 for x in tx_data if x["Decision"] == "CHALLENGE_OTP"))
m4.metric("المحظورة 🚫", sum(1 for x in tx_data if x["Decision"] == "BLOCKED"))

st.divider()

t1, t2, t3 = st.tabs([cfg["tab1"], cfg["tab2"], cfg["tab3"]])

with t1:
    with st.form("tx_input_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            u_id = st.number_input("User ID", value=1055, step=1)
            amt = st.number_input("Amount ($)", value=250.0, step=25.0)
            country = st.selectbox("Country", ["EG", "SA", "AE", "US", "UK", "FR", "DE", "CN", "UNKNOWN", "XX"])
        with col_b:
            token = st.text_input("Card Token", value="tok_card_live_998811")
            res_val = st.selectbox("Screen Res", ["1920x1080", "2560x1440", "390x844 (Mobile)", "SwiftShader VM"])
            gpu_val = st.selectbox("GPU", ["Apple M2/M3", "NVIDIA RTX 4080", "Adreno Mobile", "SwiftShader Emulator"])
            cpu_val = st.selectbox("CPU Cores", [8, 12, 16, 6, 4, 2])
        submit_tx = st.form_submit_button(cfg["btn"])

    if submit_tx:
        if not eng["security"].allow_request("client_session"):
            st.error("🚨 تم حظر الطلب مؤقتاً لتجاوز المعدل المسموح به (Rate Limit Protection).")
        else:
            t0 = time.perf_counter()
            s_tok = eng["security"].sanitize(token)
            hw = compute_hardware_hash(res_val, gpu_val, cpu_val)

            is_con, reason = eng["consortium"].check(hw, s_tok)
            if is_con:
                decision = "BLOCKED"
                risk = 100.0
                driver = reason
            elif country in {"UNKNOWN", "XX"}:
                decision = "BLOCKED"
                risk = 100.0
                driver = "دولة مدرجة بالقوائم المحظورة"
            else:
                now_ts = datetime.utcnow().timestamp()
                feats = eng["store"].process(u_id, hw, amt, country, now_ts)

                if feats["impossible_travel"]:
                    decision = "BLOCKED"
                    risk = 99.9
                    driver = f"سفر مستحيل جغرافياً ({feats['speed_kmh']} كم/س)"
                else:
                    df_in = pd.DataFrame([[feats[c] for c in eng["features"]]], columns=eng["features"])
                    is_ano = bool(eng["anomaly"].predict(df_in)[0] == -1)
                    prob = float(eng["classifier"].predict_proba(df_in)[0][1])

                    if is_ano and prob < 0.32: prob = 0.38

                    if prob >= 0.82: decision = "BLOCKED"
                    elif prob >= 0.32: decision = "CHALLENGE_OTP"
                    else: decision = "APPROVE"

                    risk = round(prob * 100, 2)
                    driver = max(eng["features"], key=lambda k: feats[k] if k != "user_time_diff" else 1.0 / (feats[k] + 1))

            lat = round((time.perf_counter() - t0) * 1000, 2)
            masked = eng["security"].mask_card(s_tok)
            sig = eng["security"].sign_audit({"user": u_id, "amt": amt, "decision": decision, "ts": now_ts if 'now_ts' in locals() else time.time()})

            st.session_state.tx_records.append({
                "Time": datetime.now().strftime("%H:%M:%S"),
                "User": u_id,
                "Card": masked,
                "HW-Hash": hw,
                "Decision": decision,
                "Risk": f"{risk}%",
                "Driver": driver,
                "Latency": f"{lat} ms",
                "Audit-Sig": sig
            })

            if decision == "BLOCKED":
                st.error(f"🚫 تم حظر المعاملة! | نسبة المخاطرة: {risk}% | السبب: {driver} | الاستجابة: {lat} ms")
            elif decision == "CHALLENGE_OTP":
                st.warning(f"⚠️ طلب رمز تحقق (OTP) | نسبة المخاطرة: {risk}% | السبب: {driver} | الاستجابة: {lat} ms")
            else:
                st.success(f"✅ تمت الموافقة على المعاملة | نسبة المخاطرة: {risk}% | السبب: {driver} | الاستجابة: {lat} ms")

    if st.session_state.tx_records:
        st.dataframe(pd.DataFrame(st.session_state.tx_records).iloc[::-1], use_container_width=True)

with t2:
    with st.form("call_test_form"):
        ph_num = st.text_input("Caller Phone", value="+201099887766")
        scenarios = {
            "احتيال مصرفي واضح": "أهلاً يا فندم أنا من خدمة عملاء البنك المركزي، حسابك موقوف ونحتاج تحديث البيانات، أمليني رقم الفيزا والـ OTP فوراً.",
            "مكالمة عمل عادية": "السلام عليكم، بخصوص ملفات المشروع هل يمكن عقد الاجتماع اليوم في تمام الساعة الرابعة؟"
        }
        picked = st.selectbox("سيناريو تجريبي:", list(scenarios.keys()))
        transcript = st.text_area("النص الصوتي المفرغ:", value=scenarios[picked], height=90)
        submit_call = st.form_submit_button(cfg["eval_call"])

    if submit_call:
        score, call_dec, matches = eng["voice"].scan(transcript)
        if call_dec == "TERMINATE_AND_BLOCK":
            eng["consortium"].report(phone=ph_num)
            st.error(f"🚨 تم قطع المكالمة وحظر الرقم فورياً! | الرقم `{ph_num}` أُضيف للقائمة السوداء | نسبة الخطر: {score}%")
        elif call_dec == "ALERT_USER":
            st.warning(f"⚠️ اشتباه احتيال: تم تنبيه العميل أثناء المكالمة | نسبة الخطر: {score}%")
        else:
            st.success(f"✅ مكالمة آمنة وطبيعية | نسبة الخطر: {score}%")

with t3:
    c_h, c_c, c_p = st.columns(3)
    c_h.metric("أجهزة محظورة دولياً", len(eng["consortium"].blocked_hw))
    c_c.metric("بطاقات مسروقة مسجلة", len(eng["consortium"].blocked_cards))
    c_p.metric("أرقام هواتف محظورة", len(eng["consortium"].blocked_phones))