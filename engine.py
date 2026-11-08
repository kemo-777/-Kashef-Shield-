import hashlib
import hmac
import html
import os
import re
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import IsolationForest
from xgboost import XGBClassifier

HMAC_SECRET = os.getenv("FRAUD_HMAC_SECRET", "bank_grade_key_2026_xyz").encode()

COUNTRY_COORDS = {
    "EG": (30.0444, 31.2357),
    "SA": (24.7136, 46.6753),
    "AE": (25.2048, 55.2708),
    "US": (37.0902, -95.7129),
    "UK": (55.3781, -3.4360),
    "FR": (46.2276, 2.2137),
    "DE": (51.1657, 10.4515),
    "CN": (35.8617, 104.1954),
    "UNKNOWN": (0.0, 0.0),
    "XX": (0.0, 0.0)
}

def haversine_distance(c1, c2):
    lat1, lon1 = np.radians(c1)
    lat2, lon2 = np.radians(c2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    return 6371.0 * (2 * np.arcsin(np.sqrt(a)))

def compute_hardware_hash(res: str, gpu: str, cores: int) -> str:
    raw = f"{res}_{gpu}_{cores}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

class CyberSecurityShield:
    def __init__(self, max_reqs: int = 100):
        self.window = 60.0
        self.max_reqs = max_reqs
        self.history: Dict[str, list] = {}

    def allow_request(self, client_id: str) -> bool:
        now = time.time()
        if client_id not in self.history:
            self.history[client_id] = []
        self.history[client_id] = [t for t in self.history[client_id] if now - t < self.window]
        if len(self.history[client_id]) >= self.max_reqs:
            return False
        self.history[client_id].append(now)
        return True

    @staticmethod
    def sanitize(text: str) -> str:
        if not isinstance(text, str):
            return str(text)
        return re.sub(r'[<>{}\;]', '', html.escape(text.strip()))

    @staticmethod
    def mask_card(token: str) -> str:
        if len(token) <= 4:
            return "****"
        return f"****-****-****-{token[-4:]}"

    @staticmethod
    def sign_audit(data: Dict[str, Any]) -> str:
        msg = f"{data.get('user')}_{data.get('amt')}_{data.get('decision')}_{data.get('ts')}"
        return hmac.new(HMAC_SECRET, msg.encode(), hashlib.sha256).hexdigest()[:16]

class GlobalConsortiumNetwork:
    def __init__(self):
        self.blocked_hw: set = set()
        self.blocked_cards: set = set()
        self.blocked_phones: set = set()

    def report(self, hw: str = None, card: str = None, phone: str = None):
        if hw: self.blocked_hw.add(hw)
        if card: self.blocked_cards.add(card)
        if phone: self.blocked_phones.add(phone)

    def check(self, hw: str, card: str) -> Tuple[bool, str]:
        if hw in self.blocked_hw:
            return True, "جهاز محظور دولياً ضمن شبكة التحالف"
        if card in self.blocked_cards:
            return True, "بطاقة مسروقة ومبلغ عنها دولياً"
        return False, ""

class VoicePhishingShield:
    PHRASES = [
        "رقم الفيزا", "رقم البطاقة", "cvv", "كود التحقق", "رمز otp", "البنك المركزي",
        "حسابك موقوف", "تحديث البيانات", "رقم الكارت", "card number", "otp code",
        "security code", "verify account", "bank security", "pin code"
    ]

    def scan(self, text: str) -> Tuple[float, str, List[str]]:
        t_low = text.lower()
        matched = [p for p in self.PHRASES if p in t_low]
        has_card = bool(re.search(r'\b(?:\d[ -]*?){13,16}\b', t_low))
        has_otp = bool(re.search(r'\b\d{4,6}\b', t_low))

        score = len(matched) * 25 + (40 if has_card else 0) + (30 if has_otp else 0)
        score = min(100.0, float(score))

        if score >= 60.0:
            decision = "TERMINATE_AND_BLOCK"
        elif score >= 30.0:
            decision = "ALERT_USER"
        else:
            decision = "ALLOW"

        return score, decision, matched

class ProductionFeatureStore:
    def __init__(self):
        self.user_history: Dict[int, List[Dict[str, Any]]] = {}
        self.hw_users: Dict[str, set] = {}

    def process(self, u_id: int, hw_hash: str, amount: float, country: str, ts: float) -> Dict[str, Any]:
        if hw_hash not in self.hw_users:
            self.hw_users[hw_hash] = set()
        self.hw_users[hw_hash].add(u_id)
        shared_count = float(len(self.hw_users[hw_hash]))

        if u_id not in self.user_history:
            self.user_history[u_id] = []
        hist = self.user_history[u_id]

        imp_travel = False
        speed_kmh = 0.0

        if len(hist) > 0:
            last = hist[-1]
            t_diff = max(1.0, ts - last["ts"])
            c_last = COUNTRY_COORDS.get(last["country"], (0.0, 0.0))
            c_curr = COUNTRY_COORDS.get(country, (0.0, 0.0))
            dist = haversine_distance(c_last, c_curr)
            
            hours = t_diff / 3600.0
            if hours > 0:
                speed_kmh = dist / hours
                if dist > 300 and speed_kmh > 900.0:
                    imp_travel = True

            amounts = [x["amount"] for x in hist]
            avg_amt = sum(amounts) / len(amounts)
            amt_ratio = min(50.0, max(0.1, amount / (avg_amt + 1e-5)))
        else:
            t_diff = 86400.0
            amt_ratio = 1.0

        hist.append({"ts": ts, "amount": amount, "country": country})
        if len(hist) > 100:
            self.user_history[u_id] = hist[-100:]

        return {
            "amount": amount,
            "user_time_diff": t_diff,
            "amount_ratio_to_history": amt_ratio,
            "device_shared_users_count": shared_count,
            "impossible_travel": imp_travel,
            "speed_kmh": round(speed_kmh, 1)
        }

def initialize_models():
    np.random.seed(42)
    n = 20000
    start = datetime(2026, 1, 1)

    timestamps = [start + timedelta(seconds=int(s)) for s in np.sort(np.random.uniform(0, 40 * 86400, n))]
    user_ids = np.random.randint(1000, 4000, size=n)
    amounts = np.random.gamma(shape=2.5, scale=40, size=n) + 5
    is_fraud = np.zeros(n, dtype=int)

    fraud_idx = np.random.choice(n, size=int(n * 0.02), replace=False)
    is_fraud[fraud_idx] = 1
    amounts[fraud_idx] = np.random.exponential(scale=700, size=len(fraud_idx)) + 25

    df = pd.DataFrame({
        "timestamp": timestamps,
        "user_id": user_ids,
        "amount": amounts,
        "is_fraud": is_fraud
    })

    df["ts_sec"] = df["timestamp"].astype("int64") // 10**9
    df["user_time_diff"] = df.groupby("user_id")["ts_sec"].diff().fillna(86400).clip(lower=1.0)
    user_avg = df.groupby("user_id")["amount"].transform(lambda x: x.expanding().mean())
    df["amount_ratio_to_history"] = (df["amount"] / (user_avg + 1e-5)).clip(0.1, 50.0)
    df["device_shared_users_count"] = 1.0

    features = ["amount", "user_time_diff", "amount_ratio_to_history", "device_shared_users_count"]

    iso = IsolationForest(n_estimators=80, contamination=0.02, random_state=42)
    iso.fit(df[features])

    ratio = float(np.sum(df["is_fraud"] == 0)) / np.sum(df["is_fraud"] == 1)
    xgb = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=ratio,
        eval_metric="aucpr",
        random_state=42,
        tree_method="hist"
    )

    # معايرة متوافقة تماماً
    calib = CalibratedClassifierCV(estimator=xgb, method="sigmoid", cv=3)
    calib.fit(df[features], df["is_fraud"])

    return iso, calib, features