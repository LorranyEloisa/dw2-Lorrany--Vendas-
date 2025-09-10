
from database import SessionLocal, Base, engine
from models import Produto
from sqlalchemy.orm.exc import NoResultFound

Base.metadata.create_all(bind=engine)

produtos = [
    {"nome": "Caderno Universitário 10 matérias", "descricao": "Caderno capa dura, 200 folhas.", "preco": 32.90, "estoque": 30, "categoria": "Cadernos", "sku": "CAD-10M"},
    {"nome": "Caderno Brochura Pequeno", "descricao": "Caderno brochura 48 folhas.", "preco": 7.50, "estoque": 50, "categoria": "Cadernos", "sku": "CAD-BRO-PEQ"},
    {"nome": "Caneta Esferográfica Azul", "descricao": "Caneta azul, escrita macia.", "preco": 2.50, "estoque": 100, "categoria": "Canetas", "sku": "CAN-AZUL"},
    {"nome": "Caneta Esferográfica Preta", "descricao": "Caneta preta, corpo transparente.", "preco": 2.50, "estoque": 80, "categoria": "Canetas", "sku": "CAN-PRETA"},
    {"nome": "Caneta Esferográfica Vermelha", "descricao": "Caneta vermelha, ponta fina.", "preco": 2.50, "estoque": 60, "categoria": "Canetas", "sku": "CAN-VERM"},
    {"nome": "Lápis Preto HB", "descricao": "Lápis preto, madeira reflorestada.", "preco": 1.20, "estoque": 120, "categoria": "Lápis", "sku": "LAPIS-HB"},
    {"nome": "Lápis de Cor 12 cores", "descricao": "Estojo com 12 lápis de cor.", "preco": 14.90, "estoque": 40, "categoria": "Lápis", "sku": "LAPIS-COR-12"},
    {"nome": "Lápis de Cor 24 cores", "descricao": "Estojo com 24 lápis de cor.", "preco": 24.90, "estoque": 30, "categoria": "Lápis", "sku": "LAPIS-COR-24"},
    {"nome": "Mochila Escolar Juvenil", "descricao": "Mochila resistente, várias cores.", "preco": 99.90, "estoque": 20, "categoria": "Mochilas", "sku": "MOCH-JUV"},
    {"nome": "Mochila Executiva", "descricao": "Mochila para notebook, preta.", "preco": 149.90, "estoque": 10, "categoria": "Mochilas", "sku": "MOCH-EXEC"},
    {"nome": "Borracha Branca", "descricao": "Borracha macia, não mancha.", "preco": 1.80, "estoque": 90, "categoria": "Acessórios", "sku": "BORR-BRANCA"},
    {"nome": "Apontador Duplo", "descricao": "Apontador com depósito.", "preco": 3.50, "estoque": 70, "categoria": "Acessórios", "sku": "APONT-DUPLO"},
    {"nome": "Régua 30cm", "descricao": "Régua plástica flexível.", "preco": 4.90, "estoque": 60, "categoria": "Acessórios", "sku": "REGUA-30"},
    {"nome": "Cola Branca 90g", "descricao": "Cola branca escolar, 90g.", "preco": 3.20, "estoque": 50, "categoria": "Acessórios", "sku": "COLA-90G"},
    {"nome": "Tesoura Escolar", "descricao": "Tesoura ponta arredondada.", "preco": 4.50, "estoque": 40, "categoria": "Acessórios", "sku": "TESOURA-ESC"},
    {"nome": "Estojo Simples", "descricao": "Estojo escolar, zíper reforçado.", "preco": 12.90, "estoque": 35, "categoria": "Acessórios", "sku": "ESTOJO-SIMP"},
    {"nome": "Marca Texto Amarelo", "descricao": "Marca texto cor amarela.", "preco": 5.90, "estoque": 55, "categoria": "Acessórios", "sku": "MT-AMARELO"},
    {"nome": "Compasso Escolar", "descricao": "Compasso com ponta protegida.", "preco": 8.90, "estoque": 25, "categoria": "Acessórios", "sku": "COMPASSO"},
    {"nome": "Bloco de Notas Adesivas", "descricao": "Bloco post-it 76x76mm.", "preco": 6.50, "estoque": 60, "categoria": "Acessórios", "sku": "BLOCO-POSTIT"},
    {"nome": "Agenda Escolar 2025", "descricao": "Agenda diária, capa dura.", "preco": 19.90, "estoque": 18, "categoria": "Acessórios", "sku": "AGENDA-2025"},
]

def seed():
    db = SessionLocal()
    for prod in produtos:
        existe = db.query(Produto).filter((Produto.nome == prod["nome"]) | (Produto.sku == prod["sku"])).first()
        if not existe:
            db.add(Produto(**prod))
    db.commit()
    db.close()

if __name__ == "__main__":
    seed()
