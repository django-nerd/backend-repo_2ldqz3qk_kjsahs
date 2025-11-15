"""
Database Schemas for IB FLIX

Each Pydantic model corresponds to a MongoDB collection. The collection name is the lowercase of the class name.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime

# --- Academy ---
class Academymodule(BaseModel):
    code: str = Field(..., description="Unique module code, e.g., DIA1, DIA2, VC, PE")
    title: str = Field(..., description="Module title")
    description: Optional[str] = Field(None, description="Short description")
    order: int = Field(0, description="Ordering index in the sidebar")
    is_active: bool = Field(True)

class Academyclass(BaseModel):
    module_code: str = Field(..., description="Reference to Academymodule.code")
    title: str
    description: Optional[str] = None
    drive_link: str = Field(..., description="Google Drive file link")
    duration_min: Optional[int] = Field(None, ge=0)
    day: Optional[str] = Field(None, description="Day label, e.g., 'Dia 1' ")
    tags: List[str] = Field(default_factory=list)

class Academyprogress(BaseModel):
    user_id: str
    class_id: str
    status: Literal['started','completed']
    progress_pct: float = Field(ge=0, le=100)

# --- Enterprise / RBAC ---
Role = Literal['admin','analista','colaborador','financeiro','treinamento']
Plan = Literal['starter','pro','corporate']

class Enterpriseorg(BaseModel):
    name: str
    plan: Plan = 'starter'
    domain: Optional[str] = None

class Enterpriseuser(BaseModel):
    org_id: str
    name: str
    email: EmailStr
    role: Role = 'colaborador'
    is_active: bool = True

class Permissionupdate(BaseModel):
    user_id: str
    role: Role
    is_active: Optional[bool] = None

class Auditlog(BaseModel):
    org_id: str
    user_id: Optional[str] = None
    action: str
    meta: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# --- Portfolio & Imports (simplified MVP) ---
class Transaction(BaseModel):
    user_id: str
    ticker: str
    quantidade: float
    preco_compra: float
    data_compra: str
    corretora: str

# --- Reports ---
class ReportRequest(BaseModel):
    user_id: str
    report_type: Literal['daily','weekly','monthly']

# --- Intelligence / Recs ---
class RecommendationRequest(BaseModel):
    user_id: str
    tickers: List[str]

class Recommendation(BaseModel):
    ticker: str
    score: int
    nivel_confianca: Literal['low','medium','high']
    racional: str
    impacto: Literal['baixo','médio','alto']
    fatores_chave: List[str]
