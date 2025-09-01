
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from models import Produto, Pedido
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
    modelo: Optional[str] = None

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
from database import engine, Base, SessionLocal
from models import Produto
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

# Adiciona produtos iniciais se o banco estiver vazio
from sqlalchemy.orm import Session as Sessao
def popular_produtos():
    db = Sessao(bind=engine)
    if db.query(Produto).count() == 0:
        produtos = [
            Produto(nome="Caderno 10 Matérias", modelo="Tilibra MaxNotes", descricao="Caderno universitário 10 matérias, 200 folhas.", preco=32.90, estoque=20, categoria="Papelaria", sku="CAD10M-TILIBRA", imagem="https://images.tcdn.com.br/img/img_prod/744006/caderno_universitario_10_materias_tilibra_200_folhas_1041_1_20201218155316.jpg"),
            Produto(nome="Lápis Preto", modelo="Faber-Castell 1201", descricao="Lápis preto sextavado.", preco=1.50, estoque=100, categoria="Escrita", sku="LAPIS-FC1201", imagem="https://images.tcdn.com.br/img/img_prod/744006/lapis_preto_faber_castell_1201_1043_1_20201218155316.jpg"),
            Produto(nome="Mochila Escolar", modelo="Sestini Up4You", descricao="Mochila resistente, várias cores.", preco=149.90, estoque=10, categoria="Acessórios", sku="MOCH-SESTINI", imagem="https://images.tcdn.com.br/img/img_prod/744006/mochila_escolar_sestini_up4you_1045_1_20201218155316.jpg"),
            Produto(nome="Borracha Branca", modelo="Mercur BR40", descricao="Borracha macia, não mancha.", preco=2.00, estoque=60, categoria="Escrita", sku="BORR-MERCUR", imagem="https://images.tcdn.com.br/img/img_prod/744006/borracha_branca_mercur_br40_1047_1_20201218155316.jpg"),
            Produto(nome="Caneta Azul", modelo="BIC Cristal", descricao="Caneta esferográfica azul.", preco=2.50, estoque=80, categoria="Escrita", sku="CANETA-BIC", imagem="https://images.tcdn.com.br/img/img_prod/744006/caneta_bic_cristal_azul_1049_1_20201218155316.jpg"),
            Produto(nome="Calculadora Científica", modelo="Casio FX-82MS", descricao="Calculadora científica 240 funções.", preco=119.00, estoque=5, categoria="Eletrônicos", sku="CALC-CASIO", imagem="https://images.tcdn.com.br/img/img_prod/744006/calculadora_cientifica_casio_fx_82ms_1051_1_20201218155316.jpg"),
            Produto(nome="Estojo Escolar", modelo="Tilibra Colors", descricao="Estojo grande, zíper reforçado.", preco=24.90, estoque=25, categoria="Acessórios", sku="ESTOJO-TILIBRA", imagem="https://images.tcdn.com.br/img/img_prod/744006/estojo_escolar_tilibra_colors_1053_1_20201218155316.jpg"),
            Produto(nome="Régua 30cm", modelo="Trident Flex", descricao="Régua flexível 30cm.", preco=4.90, estoque=40, categoria="Papelaria", sku="REGUA-TRIDENT", imagem="https://images.tcdn.com.br/img/img_prod/744006/regua_30cm_trident_flex_1055_1_20201218155316.jpg"),
            Produto(nome="Apontador Duplo", modelo="Faber-Castell Duo", descricao="Apontador com depósito.", preco=5.50, estoque=50, categoria="Acessórios", sku="APONT-FC", imagem="https://images.tcdn.com.br/img/img_prod/744006/apontador_duplo_faber_castell_duo_1057_1_20201218155316.jpg"),
            Produto(nome="Marca Texto", modelo="Stabilo Boss", descricao="Marca texto amarelo.", preco=6.90, estoque=30, categoria="Escrita", sku="MT-STABILO", imagem="https://images.tcdn.com.br/img/img_prod/744006/marca_texto_stabilo_boss_1059_1_20201218155316.jpg"),
            Produto(nome="Kit Canetas Coloridas", modelo="Faber-Castell 10 cores", descricao="Kit com 10 canetas coloridas para destacar seus estudos.", preco=14.90, estoque=40, categoria="Escrita", sku="KIT-CANETAS-FC", imagem="https://images.tcdn.com.br/img/img_prod/744006/kit_canetas_coloridas_faber_castell_1061_1_20201218155316.jpg"),
            Produto(nome="Agenda 2025", modelo="Tilibra Soho", descricao="Agenda diária 2025, capa dura, elástico.", preco=29.90, estoque=15, categoria="Papelaria", sku="AGENDA-TILIBRA", imagem="https://images.tcdn.com.br/img/img_prod/744006/agenda_tilibra_soho_2025_1063_1_20201218155316.jpg"),
            Produto(nome="Lancheira Térmica", modelo="Sestini Kids", descricao="Lancheira térmica infantil, várias estampas.", preco=39.90, estoque=12, categoria="Acessórios", sku="LANCHEIRA-SESTINI", imagem="https://images.tcdn.com.br/img/img_prod/744006/lancheira_termica_sestini_kids_1065_1_20201218155316.jpg"),
            Produto(nome="Tesoura Escolar", modelo="Mundial Soft", descricao="Tesoura escolar ponta arredondada.", preco=3.90, estoque=60, categoria="Acessórios", sku="TESOURA-MUNDIAL", imagem="https://images.tcdn.com.br/img/img_prod/744006/tesoura_escolar_mundial_soft_1067_1_20201218155316.jpg"),
            Produto(nome="Cola Branca", modelo="Acrilex 90g", descricao="Cola branca escolar, 90g.", preco=2.80, estoque=70, categoria="Papelaria", sku="COLA-ACRILEX", imagem="https://images.tcdn.com.br/img/img_prod/744006/cola_branca_acrilex_90g_1069_1_20201218155316.jpg"),
            Produto(nome="Lapiseira 0.7mm", modelo="Pentel P207", descricao="Lapiseira profissional 0.7mm.", preco=8.90, estoque=30, categoria="Escrita", sku="LAPISEIRA-PENTEL", imagem="https://images.tcdn.com.br/img/img_prod/744006/lapiseira_pentel_p207_1071_1_20201218155316.jpg"),
            Produto(nome="Bloco de Notas", modelo="Post-it 76x76mm", descricao="Bloco adesivo amarelo, 100 folhas.", preco=4.50, estoque=50, categoria="Papelaria", sku="BLOCO-POSTIT", imagem="https://images.tcdn.com.br/img/img_prod/744006/bloco_postit_76x76_1073_1_20201218155316.jpg"),
            Produto(nome="Canetinha Hidrocor", modelo="Faber-Castell 12 cores", descricao="Canetinha hidrocor lavável.", preco=13.90, estoque=35, categoria="Escrita", sku="CANETINHA-FC", imagem="https://images.tcdn.com.br/img/img_prod/744006/canetinha_faber_castell_12_cores_1075_1_20201218155316.jpg"),
            Produto(nome="Pasta Catálogo", modelo="Dello 50 plásticos", descricao="Pasta catálogo com 50 plásticos.", preco=11.90, estoque=20, categoria="Papelaria", sku="PASTA-DELLO", imagem="https://images.tcdn.com.br/img/img_prod/744006/pasta_catalogo_dello_50_1077_1_20201218155316.jpg"),
            Produto(nome="Compasso Escolar", modelo="Trident Classic", descricao="Compasso escolar com ponta protegida.", preco=7.90, estoque=18, categoria="Acessórios", sku="COMPASSO-TRIDENT", imagem="https://images.tcdn.com.br/img/img_prod/744006/compasso_trident_classic_1079_1_20201218155316.jpg"),
        ]
        db.add_all(produtos)
        db.commit()
    db.close()
popular_produtos()

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
