
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, CheckConstraint, Float
from .database import Base
from datetime import datetime


class Produto(Base):
    __tablename__ = 'produtos'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(60), nullable=False)
    descricao = Column(Text)
    preco = Column(Numeric(10, 2), nullable=False)
    estoque = Column(Integer, nullable=False)
    categoria = Column(String(40), nullable=False)
    sku = Column(String(40))
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        CheckConstraint('preco >= 0.01', name='check_preco_min'),
        CheckConstraint('estoque >= 0', name='check_estoque_min'),
    )

class Pedido(Base):
    __tablename__ = 'pedidos'
    id = Column(Integer, primary_key=True, index=True)
    total_final = Column(Float, nullable=False)
    data = Column(DateTime, default=datetime.utcnow)
