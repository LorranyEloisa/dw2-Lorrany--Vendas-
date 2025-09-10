
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from .models import Produto, Pedido
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

class CarrinhoItem(BaseModel):
    produto_id: int
    quantidade: int  # >=1

class ConfirmarCarrinhoRequest(BaseModel):
    items: list[CarrinhoItem]
    coupon: str = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

@app.post("/carrinho/confirmar")
def confirmar_carrinho(req: ConfirmarCarrinhoRequest, db: Session = Depends(get_db)):
    if not req.items:
        raise HTTPException(status_code=400, detail="Carrinho vazio.")
    produtos = db.query(Produto).filter(Produto.id.in_([item.produto_id for item in req.items])).all()
    prod_map = {p.id: p for p in produtos}
    total = Decimal('0.00')
    for item in req.items:
        if not isinstance(item.quantidade, int) or item.quantidade < 1:
            raise HTTPException(status_code=400, detail=f"Quantidade inválida para produto id {item.produto_id}.")
        prod = prod_map.get(item.produto_id)
        if not prod:
            raise HTTPException(status_code=400, detail=f"Produto id {item.produto_id} não encontrado.")
        if prod.estoque < item.quantidade:
            raise HTTPException(status_code=400, detail=f"Estoque insuficiente para '{prod.nome}'.")
        total += Decimal(str(prod.preco)) * Decimal(item.quantidade)
    total = total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    discount = Decimal('0.00')
    if req.coupon and req.coupon.upper() == 'ALUNO10':
        discount = (total * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_final = (total - discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    # Reduz estoque
    for item in req.items:
        prod = prod_map[item.produto_id]
        prod.estoque -= item.quantidade
    # Cria pedido (opcional simplificado)
    from datetime import datetime
    pedido = Pedido(
        data=datetime.now(),
        total_final=float(total_final)
    )
    db.add(pedido)
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao salvar pedido.")
    return {
        "order_id": pedido.id,
        "total_before": float(total),
        "discount": float(discount),
        "total_final": float(total_final)
    }


from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from .models import Produto
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

# --- Pydantic Schemas ---
class ProdutoBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=60)
    descricao: Optional[str] = None
    preco: float = Field(..., ge=0.01)
    estoque: int = Field(..., ge=0)
    categoria: str = Field(...)
    sku: Optional[str] = None

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=60)
    descricao: Optional[str] = None
    preco: Optional[float] = Field(None, ge=0.01)
    estoque: Optional[int] = Field(None, ge=0)
    categoria: Optional[str] = None
    sku: Optional[str] = None

class ProdutoRead(ProdutoBase):
    id: int
    created_at: Optional[datetime]
    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints REST Produto ---
@app.get("/produtos", response_model=List[ProdutoRead])
def listar_produtos(
    search: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
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
        produtos = query.offset((page-1)*limit).limit(limit).all()
        return produtos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar produtos: {str(e)}")

@app.get("/produtos/{id}", response_model=ProdutoRead)
def get_produto(id: int, db: Session = Depends(get_db)):
    prod = db.query(Produto).filter(Produto.id == id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return prod

@app.post("/produtos", response_model=ProdutoRead, status_code=201)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    try:
        db_prod = Produto(**produto.dict())
        db.add(db_prod)
        db.commit()
        db.refresh(db_prod)
        return db_prod
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar produto: {str(e)}")

@app.put("/produtos/{id}", response_model=ProdutoRead)
def atualizar_produto(id: int, produto: ProdutoUpdate, db: Session = Depends(get_db)):
    db_prod = db.query(Produto).filter(Produto.id == id).first()
    if not db_prod:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    data = produto.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(db_prod, key, value)
    try:
        db.commit()
        db.refresh(db_prod)
        return db_prod
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar produto: {str(e)}")

@app.delete("/produtos/{id}", status_code=204)
def deletar_produto(id: int, db: Session = Depends(get_db)):
    db_prod = db.query(Produto).filter(Produto.id == id).first()
    if not db_prod:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    try:
        db.delete(db_prod)
        db.commit()
        return JSONResponse(status_code=204, content=None)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar produto: {str(e)}")

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
            # Novos produtos e categorias
            Produto(nome="Garrafa Térmica", modelo="Stanley Classic", descricao="Garrafa térmica 1L, mantém a temperatura por 24h.", preco=99.90, estoque=15, categoria="Acessórios", sku="GARRAFA-STANLEY", imagem="https://images.tcdn.com.br/img/img_prod/744006/garrafa_termica_stanley_1l_1081_1_20201218155316.jpg"),
            Produto(nome="Tablet Educacional", modelo="Samsung Tab A7", descricao="Tablet para estudos, tela 10.4''.", preco=899.00, estoque=8, categoria="Eletrônicos", sku="TABLET-SAMSUNG", imagem="https://images.tcdn.com.br/img/img_prod/744006/tablet_samsung_tab_a7_1083_1_20201218155316.jpg"),
            Produto(nome="Livro Didático Matemática", modelo="Moderna 2025", descricao="Livro didático completo para o ensino fundamental.", preco=74.90, estoque=20, categoria="Livros", sku="LIVRO-MATEMATICA", imagem="https://images.tcdn.com.br/img/img_prod/744006/livro_didatico_matematica_1085_1_20201218155316.jpg"),
            Produto(nome="Pen Drive 32GB", modelo="Kingston DataTraveler", descricao="Pen drive USB 3.0, 32GB.", preco=29.90, estoque=30, categoria="Eletrônicos", sku="PENDRIVE-KINGSTON", imagem="https://images.tcdn.com.br/img/img_prod/744006/pendrive_kingston_32gb_1087_1_20201218155316.jpg"),
            Produto(nome="Camiseta Escolar", modelo="Uniforme Oficial 2025", descricao="Camiseta escolar algodão, tamanhos variados.", preco=39.90, estoque=25, categoria="Uniformes", sku="CAMISETA-ESCOLAR", imagem="https://images.tcdn.com.br/img/img_prod/744006/camiseta_escolar_uniforme_1089_1_20201218155316.jpg"),
            Produto(nome="Tênis Escolar", modelo="Olympikus Infantil", descricao="Tênis escolar confortável, do 28 ao 36.", preco=119.90, estoque=18, categoria="Uniformes", sku="TENIS-OLYMPIKUS", imagem="https://images.tcdn.com.br/img/img_prod/744006/tenis_escolar_olympikus_1091_1_20201218155316.jpg"),
            Produto(nome="Fichário Universitário", modelo="Dac Trendy", descricao="Fichário com 96 folhas e divisórias.", preco=49.90, estoque=12, categoria="Papelaria", sku="FICHARIO-DAC", imagem="https://images.tcdn.com.br/img/img_prod/744006/fichario_universitario_dac_1093_1_20201218155316.jpg"),
            Produto(nome="Mochila Executiva", modelo="Swissland Pro", descricao="Mochila para notebook, resistente à água.", preco=199.90, estoque=7, categoria="Acessórios", sku="MOCHILA-SWISSLAND", imagem="https://images.tcdn.com.br/img/img_prod/744006/mochila_executiva_swissland_1095_1_20201218155316.jpg"),
            Produto(nome="Livro de Redação", modelo="Foco ENEM 2025", descricao="Livro de redação com temas e correção comentada.", preco=59.90, estoque=14, categoria="Livros", sku="LIVRO-REDACAO", imagem="https://images.tcdn.com.br/img/img_prod/744006/livro_redacao_enem_1097_1_20201218155316.jpg"),
            Produto(nome="Mouse Sem Fio", modelo="Logitech M170", descricao="Mouse wireless, bateria de longa duração.", preco=49.90, estoque=22, categoria="Eletrônicos", sku="MOUSE-LOGITECH", imagem="https://images.tcdn.com.br/img/img_prod/744006/mouse_logitech_m170_1099_1_20201218155316.jpg"),
            Produto(nome="Caderno de Desenho", modelo="Tilibra Art", descricao="Caderno para desenho, 96 folhas.", preco=19.90, estoque=16, categoria="Papelaria", sku="CADERNO-DESENHO", imagem="https://images.tcdn.com.br/img/img_prod/744006/caderno_desenho_tilibra_1101_1_20201218155316.jpg"),
            Produto(nome="Dicionário Escolar", modelo="Aurélio Mini", descricao="Dicionário escolar compacto.", preco=27.90, estoque=20, categoria="Livros", sku="DICIONARIO-AURELIO", imagem="https://images.tcdn.com.br/img/img_prod/744006/dicionario_aurelio_mini_1103_1_20201218155316.jpg"),
            Produto(nome="Bloco de Fichas", modelo="Spiral 5x8", descricao="Bloco com 100 fichas pautadas.", preco=7.90, estoque=30, categoria="Papelaria", sku="BLOCO-FICHAS", imagem="https://images.tcdn.com.br/img/img_prod/744006/bloco_fichas_spiral_1105_1_20201218155316.jpg"),
            Produto(nome="Lancheira Térmica Star", modelo="Sestini Star", descricao="Lancheira térmica com estampa de estrelas.", preco=44.90, estoque=10, categoria="Acessórios", sku="LANCHEIRA-STAR", imagem="https://images.tcdn.com.br/img/img_prod/744006/lancheira_termica_star_1107_1_20201218155316.jpg"),
            Produto(nome="Estojo Triplo", modelo="Tilibra Max", descricao="Estojo escolar triplo, grande capacidade.", preco=29.90, estoque=18, categoria="Acessórios", sku="ESTOJO-TRIPLO", imagem="https://images.tcdn.com.br/img/img_prod/744006/estojo_triplo_tilibra_1109_1_20201218155316.jpg"),
            Produto(nome="Livro Inglês Básico", modelo="Oxford Basic", descricao="Livro didático de inglês para iniciantes.", preco=69.90, estoque=12, categoria="Livros", sku="LIVRO-INGLES", imagem="https://images.tcdn.com.br/img/img_prod/744006/livro_ingles_oxford_1111_1_20201218155316.jpg"),
            Produto(nome="Caderno Inteligente", modelo="CI Smart", descricao="Caderno inteligente com folhas removíveis.", preco=59.90, estoque=10, categoria="Papelaria", sku="CADERNO-INTELIGENTE", imagem="https://images.tcdn.com.br/img/img_prod/744006/caderno_inteligente_ci_1113_1_20201218155316.jpg"),
            Produto(nome="Tênis Esportivo", modelo="Adidas Runfalcon", descricao="Tênis esportivo para educação física.", preco=179.90, estoque=9, categoria="Uniformes", sku="TENIS-ADIDAS", imagem="https://images.tcdn.com.br/img/img_prod/744006/tenis_adidas_runfalcon_1115_1_20201218155316.jpg"),
            Produto(nome="Kit Geometria", modelo="Trident Pro", descricao="Kit com régua, compasso, transferidor e esquadros.", preco=24.90, estoque=20, categoria="Acessórios", sku="KIT-GEOMETRIA", imagem="https://images.tcdn.com.br/img/img_prod/744006/kit_geometria_trident_1117_1_20201218155316.jpg"),
            # Exemplo de produto sem imagem específica
            Produto(nome="Porta Lápis", modelo="Acrimet Colors", descricao="Porta lápis de mesa, várias cores.", preco=8.90, estoque=30, categoria="Acessórios", sku="PORTA-LAPIS", imagem="https://images.tcdn.com.br/img/img_prod/744006/porta_lapis_acrimet_1120_1_20201218155316.jpg"),
            # Cadernos femininos com variações de capa
            Produto(nome="Caderno Espiral Feminino", modelo="Make it Happen - Rosa", descricao="Caderno universitário capa dura, 96 folhas, rosa com bolinhas.", preco=29.90, estoque=15, categoria="Papelaria", sku="CAD-FEM-ROSA", imagem="https://raw.githubusercontent.com/LorranyEloisa/dw2-Lorrany--Vendas-/master/frontend/cadernos-femininos.jpg"),
            Produto(nome="Caderno Espiral Feminino", modelo="Great Start - Verde", descricao="Caderno universitário capa dura, 96 folhas, verde com bolinhas.", preco=29.90, estoque=10, categoria="Papelaria", sku="CAD-FEM-VERDE", imagem="https://raw.githubusercontent.com/LorranyEloisa/dw2-Lorrany--Vendas-/master/frontend/cadernos-femininos.jpg"),
            Produto(nome="Caderno Espiral Feminino", modelo="Listrado Rosa e Branco", descricao="Caderno universitário capa dura, 96 folhas, listrado rosa e branco.", preco=29.90, estoque=8, categoria="Papelaria", sku="CAD-FEM-LISTRADO", imagem="https://raw.githubusercontent.com/LorranyEloisa/dw2-Lorrany--Vendas-/master/frontend/cadernos-femininos.jpg"),
            # Novos produtos variados
            Produto(nome="Caneta Gel Colorida", modelo="Pilot PopLol Azul", descricao="Caneta gel azul, escrita macia.", preco=6.50, estoque=40, categoria="Escrita", sku="CANETA-GEL-AZUL", imagem="https://images.tcdn.com.br/img/img_prod/744006/caneta_gel_pilot_poplol_azul_1122_1_20201218155316.jpg"),
            Produto(nome="Caneta Gel Colorida", modelo="Pilot PopLol Rosa", descricao="Caneta gel rosa, escrita macia.", preco=6.50, estoque=35, categoria="Escrita", sku="CANETA-GEL-ROSA", imagem="https://images.tcdn.com.br/img/img_prod/744006/caneta_gel_pilot_poplol_rosa_1124_1_20201218155316.jpg"),
            Produto(nome="Mochila Juvenil", modelo="Sestini Colors Azul", descricao="Mochila escolar azul, resistente à água.", preco=139.90, estoque=12, categoria="Acessórios", sku="MOCHILA-JUVENIL-AZUL", imagem="https://images.tcdn.com.br/img/img_prod/744006/mochila_juvenil_sestini_azul_1126_1_20201218155316.jpg"),
            Produto(nome="Mochila Juvenil", modelo="Sestini Colors Rosa", descricao="Mochila escolar rosa, resistente à água.", preco=139.90, estoque=10, categoria="Acessórios", sku="MOCHILA-JUVENIL-ROSA", imagem="https://images.tcdn.com.br/img/img_prod/744006/mochila_juvenil_sestini_rosa_1128_1_20201218155316.jpg"),
            Produto(nome="Marca Texto Pastel", modelo="Stabilo Boss Lilás", descricao="Marca texto cor lilás, ponta chanfrada.", preco=7.90, estoque=25, categoria="Escrita", sku="MT-PASTEL-LILAS", imagem="https://images.tcdn.com.br/img/img_prod/744006/marca_texto_stabilo_boss_lilas_1130_1_20201218155316.jpg"),
            Produto(nome="Marca Texto Pastel", modelo="Stabilo Boss Verde", descricao="Marca texto cor verde pastel, ponta chanfrada.", preco=7.90, estoque=20, categoria="Escrita", sku="MT-PASTEL-VERDE", imagem="https://images.tcdn.com.br/img/img_prod/744006/marca_texto_stabilo_boss_verde_1132_1_20201218155316.jpg"),
            Produto(nome="Estojo Duplo", modelo="Tilibra Pink", descricao="Estojo escolar duplo, cor pink.", preco=34.90, estoque=14, categoria="Acessórios", sku="ESTOJO-DUPLO-PINK", imagem="https://images.tcdn.com.br/img/img_prod/744006/estojo_duplo_tilibra_pink_1134_1_20201218155316.jpg"),
            Produto(nome="Estojo Duplo", modelo="Tilibra Azul", descricao="Estojo escolar duplo, cor azul.", preco=34.90, estoque=16, categoria="Acessórios", sku="ESTOJO-DUPLO-AZUL", imagem="https://images.tcdn.com.br/img/img_prod/744006/estojo_duplo_tilibra_azul_1136_1_20201218155316.jpg"),
            Produto(nome="Lancheira Infantil", modelo="Sestini Dino", descricao="Lancheira térmica infantil, estampa de dinossauro.", preco=49.90, estoque=9, categoria="Acessórios", sku="LANCHEIRA-DINO", imagem="https://images.tcdn.com.br/img/img_prod/744006/lancheira_infantil_sestini_dino_1138_1_20201218155316.jpg"),
            Produto(nome="Lancheira Infantil", modelo="Sestini Unicórnio", descricao="Lancheira térmica infantil, estampa de unicórnio.", preco=49.90, estoque=7, categoria="Acessórios", sku="LANCHEIRA-UNICORNIO", imagem="https://images.tcdn.com.br/img/img_prod/744006/lancheira_infantil_sestini_unicornio_1140_1_20201218155316.jpg"),
            Produto(nome="Kit Lápis de Cor", modelo="Faber-Castell 24 cores", descricao="Kit com 24 lápis de cor, cores vivas.", preco=22.90, estoque=20, categoria="Escrita", sku="LAPIS-COR-24", imagem="https://images.tcdn.com.br/img/img_prod/744006/lapis_cor_faber_castell_24_cores_1142_1_20201218155316.jpg"),
            Produto(nome="Kit Lápis de Cor", modelo="Faber-Castell 36 cores", descricao="Kit com 36 lápis de cor, cores vivas.", preco=32.90, estoque=15, categoria="Escrita", sku="LAPIS-COR-36", imagem="https://images.tcdn.com.br/img/img_prod/744006/lapis_cor_faber_castell_36_cores_1144_1_20201218155316.jpg"),
        ]
        db.add_all(produtos)
        db.commit()
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
