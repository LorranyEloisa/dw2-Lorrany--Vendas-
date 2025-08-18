
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from .models import Produto, Pedido
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

class ProdutoSchema(BaseModel):
    nome: str = Field(..., min_length=3, max_length=60)
    descricao: Optional[str] = None
    preco: float = Field(..., ge=0.01)
    estoque: int = Field(..., ge=0)
    categoria: str = Field(...)
    sku: Optional[str] = None

class ProdutoOut(ProdutoSchema):
    id: int
    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/produtos", response_model=List[ProdutoOut])
def listar_produtos(
    search: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Produto)
    if search:
        query = query.filter(Produto.nome.ilike(f"%{search}%"))
    if categoria:
        query = query.filter(Produto.categoria == categoria)
    if sort == "preco_asc":
        query = query.order_by(Produto.preco.asc())
    elif sort == "preco_desc":
        query = query.order_by(Produto.preco.desc())
    elif sort == "nome":
        query = query.order_by(Produto.nome.asc())
    return query.all()

@app.post("/produtos", response_model=ProdutoOut, status_code=201)
def criar_produto(produto: ProdutoSchema, db: Session = Depends(get_db)):
    db_prod = Produto(**produto.dict())
    db.add(db_prod)
    db.commit()
    db.refresh(db_prod)
    return db_prod

@app.put("/produtos/{id}", response_model=ProdutoOut)
def atualizar_produto(id: int, produto: ProdutoSchema, db: Session = Depends(get_db)):
    db_prod = db.query(Produto).filter(Produto.id == id).first()
    if not db_prod:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    for key, value in produto.dict().items():
        setattr(db_prod, key, value)
    db.commit()
    db.refresh(db_prod)
    return db_prod

@app.delete("/produtos/{id}", status_code=204)
def deletar_produto(id: int, db: Session = Depends(get_db)):
    db_prod = db.query(Produto).filter(Produto.id == id).first()
    if not db_prod:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(db_prod)
    db.commit()
    return JSONResponse(status_code=204, content=None)

class ItemCarrinho(BaseModel):
    id: int
    quantidade: int = Field(..., ge=1)

class PedidoOut(BaseModel):
    id: int
    total_final: float
    data: datetime
    class Config:
        orm_mode = True

@app.post("/carrinho/confirmar", response_model=PedidoOut)
def confirmar_pedido(
    itens: List[ItemCarrinho],
    cupom: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if not itens:
        raise HTTPException(status_code=400, detail="Carrinho vazio")
    total = 0.0
    for item in itens:
        prod = db.query(Produto).filter(Produto.id == item.id).first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Produto id {item.id} não encontrado")
        if prod.estoque < item.quantidade:
            raise HTTPException(status_code=400, detail=f"Estoque insuficiente para {prod.nome}")
        total += prod.preco * item.quantidade
    desconto = 0.0
    if cupom and cupom.upper() == "ALUNO10":
        desconto = total * 0.10
    total_final = round(total - desconto, 2)
    # Baixar estoque
    for item in itens:
        prod = db.query(Produto).filter(Produto.id == item.id).first()
        prod.estoque -= item.quantidade
    pedido = Pedido(total_final=total_final)
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from .models import Produto
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

class ProdutoSchema(BaseModel):
    nome: str = Field(..., min_length=3, max_length=60)
    descricao: Optional[str] = None
    preco: float = Field(..., ge=0.01)
    estoque: int = Field(..., ge=0)
    categoria: str = Field(...)
    sku: Optional[str] = None

class ProdutoOut(ProdutoSchema):
    id: int
    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/produtos", response_model=List[ProdutoOut])
def listar_produtos(
    search: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    db: Session = next(get_db())
):
    query = db.query(Produto)
    if search:
        query = query.filter(Produto.nome.ilike(f"%{search}%"))
    if categoria:
        query = query.filter(Produto.categoria == categoria)
    if sort == "preco_asc":
        query = query.order_by(Produto.preco.asc())
    elif sort == "preco_desc":
        query = query.order_by(Produto.preco.desc())
    elif sort == "nome":
        query = query.order_by(Produto.nome.asc())
    return query.all()

@app.post("/produtos", response_model=ProdutoOut, status_code=201)
def criar_produto(produto: ProdutoSchema, db: Session = next(get_db())):
    db_prod = Produto(**produto.dict())
    db.add(db_prod)
    db.commit()
    db.refresh(db_prod)
    return db_prod

@app.put("/produtos/{id}", response_model=ProdutoOut)
def atualizar_produto(id: int, produto: ProdutoSchema, db: Session = next(get_db())):
    db_prod = db.query(Produto).filter(Produto.id == id).first()
    if not db_prod:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    for key, value in produto.dict().items():
        setattr(db_prod, key, value)
    db.commit()
    db.refresh(db_prod)
    return db_prod

@app.delete("/produtos/{id}", status_code=204)
def deletar_produto(id: int, db: Session = next(get_db())):
    db_prod = db.query(Produto).filter(Produto.id == id).first()
    if not db_prod:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(db_prod)
    db.commit()
    return JSONResponse(status_code=204, content=None)
