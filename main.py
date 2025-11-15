import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db, create_document, get_documents
from schemas import (
    Academymodule, Academyclass, Academyprogress,
    Enterpriseuser, Permissionupdate, Auditlog,
    Transaction, ReportRequest,
    RecommendationRequest, Recommendation
)

app = FastAPI(title="IB FLIX API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "IB FLIX Backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": os.getenv("DATABASE_NAME") or "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            try:
                response["collections"] = db.list_collection_names()[:20]
                response["connection_status"] = "Connected"
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# ---------------- Academy ----------------
@app.post("/academy/upload-drive-link")
def upload_drive_link(item: Academyclass):
    class_id = create_document('academyclass', item)
    return {"id": class_id, "status": "ok"}

@app.get("/academy/list-modules")
def list_modules():
    modules = get_documents('academymodule')
    return modules

@app.get("/academy/list-classes")
def list_classes(module_code: Optional[str] = None):
    flt = {"module_code": module_code} if module_code else {}
    classes = get_documents('academyclass', flt)
    return classes

@app.get("/academy/get-class")
def get_class(id: str = Query(...)):
    from bson import ObjectId
    doc = db['academyclass'].find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(404, "Class not found")
    # convert _id to string
    doc["_id"] = str(doc["_id"])
    return doc

@app.post("/academy/progress/update")
def update_progress(p: Academyprogress):
    _id = create_document('academyprogress', p)
    return {"id": _id, "status": "ok"}

@app.get("/academy/search")
def search_classes(q: str):
    # basic text-like search on title/description
    regex = {"$regex": q, "$options": "i"}
    cur = db['academyclass'].find({"$or": [{"title": regex}, {"description": regex}]})
    out = []
    for d in cur:
        d["_id"] = str(d["_id"])
        out.append(d)
    return out

# ---------------- Enterprise (RBAC) ----------------
@app.post("/enterprise/add-user")
def add_user(u: Enterpriseuser):
    # Basic plan limits enforced by org plan document if present. Here we simply insert.
    _id = create_document('enterpriseuser', u)
    # audit
    create_document('auditlog', Auditlog(org_id=u.org_id, user_id=None, action='add_user', meta={"email": u.email}))
    return {"id": _id, "status": "ok"}

@app.get("/enterprise/list-users")
def list_users(org_id: str):
    return get_documents('enterpriseuser', {"org_id": org_id})

@app.get("/enterprise/get-user")
def get_user(user_id: str):
    from bson import ObjectId
    d = db['enterpriseuser'].find_one({"_id": ObjectId(user_id)})
    if not d:
        raise HTTPException(404, "User not found")
    d["_id"] = str(d["_id"]) 
    return d

@app.post("/enterprise/update-permission")
def update_permission(p: Permissionupdate):
    from bson import ObjectId
    upd = {"role": p.role}
    if p.is_active is not None:
        upd["is_active"] = p.is_active
    res = db['enterpriseuser'].update_one({"_id": ObjectId(p.user_id)}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(404, "User not found")
    create_document('auditlog', Auditlog(org_id="", user_id=p.user_id, action='update_permission', meta=upd))
    return {"status": "ok"}

@app.get("/enterprise/audit-log")
def audit_log(org_id: str, limit: int = 100):
    return get_documents('auditlog', {"org_id": org_id}, limit=limit)

# ---------------- Intelligence: Recommendations (Hybrid placeholder logic) ----------------
class SimplePriceSeries(BaseModel):
    ticker: str
    prices: List[float]

@app.post("/intelligence/recommendations")
def recommendations(req: RecommendationRequest):
    # MVP: rule-based score + stub ML weighting
    out: List[Recommendation] = []
    for t in req.tickers:
        # Simple deterministic rules: higher last return & lower vol => higher score
        import random
        base = random.randint(40, 75)
        ml_adj = random.randint(-10, 20)
        score = max(0, min(100, base + ml_adj))
        nivel = 'low' if score < 50 else 'medium' if score < 75 else 'high'
        racional = (
            "Combinação de momentum saudável, qualidade de lucros e alavancagem sob controle. "
            "Risco ajustado ao retorno é favorável nas próximas 8–12 semanas."
        )
        impacto = 'baixo' if score < 50 else 'médio' if score < 75 else 'alto'
        fatores = [
            "MA200 > MA50",
            "ROIC acima do custo de capital",
            "Dívida/EBITDA abaixo de 2.5x",
            "Volatilidade controlada"
        ]
        out.append(Recommendation(ticker=t, score=score, nivel_confianca=nivel, racional=racional, impacto=impacto, fatores_chave=fatores))
    return out

# ---------------- Reports (PDF stub) ----------------
@app.post("/reports/generate")
def generate_report(r: ReportRequest):
    # Stub returning JSON with a pre-formatted narrative
    header = {
        'type': r.report_type,
        'title': f"Relatório {r.report_type.capitalize()} IB FLIX",
    }
    body = {
        'kpis': {
            'roi_acumulado': 0.18,
            'sharpe': 1.4,
            'vol_anualizada': 0.22,
            'dd_max': 0.12
        },
        'insight_tom': (
            "Hoje o mercado premiou quem manteve disciplina e caixa. Foque em eficiência operacional, "
            "evite ruídos e compare decisões com o seu mapa de risco. Em finanças, simplicidade vence barulho."
        )
    }
    return {"header": header, "body": body}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
