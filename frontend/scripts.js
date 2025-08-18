
const API_URL = 'http://localhost:8000';

// Renderiza lista de produtos
async function carregarProdutos() {
	const res = await fetch(`${API_URL}/produtos`);
	const produtos = await res.json();
	const lista = document.getElementById('product-list');
	lista.innerHTML = '';
	produtos.forEach(produto => {
		const card = document.createElement('div');
		card.className = 'card';
		card.innerHTML = `
			<img src="https://via.placeholder.com/100x100?text=Produto" alt="Imagem do produto">
			<div class="name">${produto.nome}</div>
			<div class="price">R$ ${produto.preco.toFixed(2)}</div>
			<div class="stock">${produto.estoque > 0 ? 'Em estoque' : 'Esgotado'}</div>
			<button ${produto.estoque === 0 ? 'disabled' : ''} aria-pressed="false" aria-label="Adicionar ao carrinho">Adicionar</button>
		`;
		lista.appendChild(card);
	});
}

window.addEventListener('DOMContentLoaded', carregarProdutos);
