import time
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from engine import ProductionFeatureStore, initialize_models

app = FastAPI(
    title="Global Fraud Intelligence Core",
    version="3.0.0",
    description="نظام بنكي متكامل لمكافحة الاحتيال مع تدقيق العمليات ولوحة تحكم حية"
)

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
VALID_API_KEY = "sk_live_global_banking_fraud_secure_key"

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != VALID_API_KEY:
        raise HTTPException(status_code=403, detail="غير مصرح: مفتاح الوصول غير صالح")
    return api_key

print("[*] جاري تدريب وتهيئة محرك المخاطر المصرفي...")
anomaly_model, classifier_model, feature_cols = initialize_models()
feature_store = ProductionFeatureStore()

BLOCK_THRESHOLD = 0.82
OTP_THRESHOLD = 0.32
audit_logs: List[Dict[str, Any]] = []

class TransactionRequest(BaseModel):
    transaction_id: str = Field(..., example="tx_987654321")
    user_id: int = Field(..., gt=0, example=1055)
    device_id: int = Field(..., gt=0, example=99999)
    amount: float = Field(..., gt=0, example=1200.0)
    country: str = Field(..., min_length=2, max_length=10, example="EG")

class DecisionResponse(BaseModel):
    transaction_id: str
    decision: str
    risk_score_pct: float
    is_anomaly: bool
    top_driver: str
    latency_ms: float

@app.post("/v1/evaluate", response_model=DecisionResponse, dependencies=[Depends(verify_api_key)])
def evaluate_transaction(payload: TransactionRequest):
    t0 = time.perf_counter()
    country = payload.country.upper()

    # 1. طبقة القواعد القطعية الفورية (0-1 مللي ثانية)
    if country in {"UNKNOWN", "XX"}:
        res = {
            "transaction_id": payload.transaction_id,
            "decision": "BLOCKED",
            "risk_score_pct": 100.0,
            "is_anomaly": True,
            "top_driver": "high_risk_country_rule",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2)
        }
        audit_logs.append({**payload.dict(), **res, "timestamp": datetime.now().isoformat()})
        return res

    # 2. جلب وتحديث الميزات اللحظية
    now_ts = datetime.utcnow().timestamp()
    feats = feature_store.get_and_update(
        user_id=payload.user_id,
        device_id=payload.device_id,
        amount=payload.amount,
        current_ts=now_ts
    )

    df_in = pd.DataFrame([[feats[c] for c in feature_cols]], columns=feature_cols)

    # 3. الفحص الهجين الذكي
    is_anomaly = bool(anomaly_model.predict(df_in)[0] == -1)
    prob = float(classifier_model.predict_proba(df_in)[0][1])

    if is_anomaly and prob < OTP_THRESHOLD:
        prob = OTP_THRESHOLD + 0.05

    # 4. اتخاذ القرار
    if prob >= BLOCK_THRESHOLD:
        decision = "BLOCKED"
    elif prob >= OTP_THRESHOLD:
        decision = "CHALLENGE_OTP"
    else:
        decision = "APPROVE"

    driver = max(feats, key=lambda k: feats[k] if k != "user_time_diff" else 1.0 / (feats[k] + 1))
    latency = round((time.perf_counter() - t0) * 1000, 2)

    result = {
        "transaction_id": payload.transaction_id,
        "decision": decision,
        "risk_score_pct": round(prob * 100, 2),
        "is_anomaly": is_anomaly,
        "top_driver": driver,
        "latency_ms": latency
    }

    audit_logs.append({**payload.dict(), **result, "timestamp": datetime.now().isoformat()})
    return result

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    total_tx = len(audit_logs)
    blocked_count = sum(1 for x in audit_logs if x.get("decision") == "BLOCKED")
    otp_count = sum(1 for x in audit_logs if x.get("decision") == "CHALLENGE_OTP")
    approved_count = sum(1 for x in audit_logs if x.get("decision") == "APPROVE")
    
    rows = ""
    for log in reversed(audit_logs[-15:]):
        color = "#e63946" if log["decision"] == "BLOCKED" else ("#f4a261" if log["decision"] == "CHALLENGE_OTP" else "#2a9d8f")
        rows += f"""
        <tr>
            <td>{log.get('transaction_id')}</td>
            <td>{log.get('user_id')}</td>
            <td>${log.get('amount'):,.2f}</td>
            <td>{log.get('country')}</td>
            <td style="color: {color}; font-weight: bold;">{log.get('decision')}</td>
            <td>{log.get('risk_score_pct')}%</td>
            <td>{log.get('top_driver')}</td>
            <td>{log.get('latency_ms')} ms</td>
        </tr>
        """

    table_body = rows if rows else "<tr><td colspan='8' style='text-align:center;'>لا توجد معاملات مسجلة بعد</td></tr>"

    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="utf-8">
        <title>لوحة مراقبة الاحتيال البنكي</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 25px; }}
            .cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
            .card {{ background: #1e293b; padding: 20px; border-radius: 10px; border: 1px solid #334155; text-align: center; }}
            .card h3 {{ margin: 0 0 10px 0; font-size: 14px; color: #94a3b8; }}
            .card .num {{ font-size: 28px; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 10px; overflow: hidden; }}
            th, td {{ padding: 12px 16px; text-align: right; border-bottom: 1px solid #334155; }}
            th {{ background: #334155; color: #cbd5e1; font-weight: 600; }}
            tr:hover {{ background: #243248; }}
        </style>
    </head>
    <body>
        <h2>لوحة التحكم المباشرة - مراقبة مخاطر العمليات</h2>
        <div class="cards">
            <div class="card"><h3>إجمالي العمليات</h3><div class="num">{total_tx}</div></div>
            <div class="card"><h3>المعاملات المقبولة</h3><div class="num" style="color: #2a9d8f;">{approved_count}</div></div>
            <div class="card"><h3>المحولة للتحقق (OTP)</h3><div class="num" style="color: #f4a261;">{otp_count}</div></div>
            <div class="card"><h3>المحظورة كلياً</h3><div class="num" style="color: #e63946;">{blocked_count}</div></div>
        </div>
        <h3>آخر 15 معاملة مسجلة في الوقت الفعلي:</h3>
        <table>
            <thead>
                <tr>
                    <th>معرف المعاملة</th>
                    <th>العميل</th>
                    <th>المبلغ</th>
                    <th>الدولة</th>
                    <th>القرار</th>
                    <th>درجة الخطورة</th>
                    <th>العامل الأبرز</th>
                    <th>زمن الاستجابة</th>
                </tr>
            </thead>
            <tbody>{table_body}</tbody>
        </table>
    </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    import uvicorn
    print("\n[+] الخادم يعمل بنجاح على: http://localhost:8000")
    print("[+] لوحة المراقبة الحية: http://localhost:8000/dashboard\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)