
from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime

class Produto(Base):
    __tablename__ = 'produtos'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(60), nullable=False)
    descricao = Column(String(255))
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, nullable=False)
    categoria = Column(String(40), nullable=False)
    sku = Column(String(40))
    modelo = Column(String(60))  # Novo campo

class Pedido(Base):
    __tablename__ = 'pedidos'
    id = Column(Integer, primary_key=True, index=True)
    total_final = Column(Float, nullable=False)
    data = Column(DateTime, default=datetime.utcnow)
