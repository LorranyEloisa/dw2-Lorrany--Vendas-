
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
			<div class="model">Modelo: <b>${produto.modelo || '-'}</b></div>
			<div class="desc">${produto.descricao || ''}</div>
			<div class="price">R$ ${produto.preco.toFixed(2)}</div>
			<div class="stock">${produto.estoque > 0 ? 'Em estoque' : 'Esgotado'}</div>
			<button ${produto.estoque === 0 ? 'disabled' : ''} aria-pressed="false" aria-label="Adicionar ao carrinho">Adicionar</button>
		`;
		lista.appendChild(card);
	});
}

window.addEventListener('DOMContentLoaded', carregarProdutos);

// Carrinho de compras
let carrinho = [];

// Atualiza contador do carrinho
function atualizarContador() {
	document.getElementById('cart-count').textContent = carrinho.reduce((acc, item) => acc + item.qtd, 0);
}

// Salva carrinho no localStorage
function salvarCarrinho() {
	localStorage.setItem('carrinho', JSON.stringify(carrinho));
}

// Carrega carrinho do localStorage
function carregarCarrinho() {
	const salvo = localStorage.getItem('carrinho');
	if (salvo) {
		carrinho = JSON.parse(salvo);
		atualizarContador();
	}
}

// Adiciona produto ao carrinho
function adicionarAoCarrinho(produto) {
	const idx = carrinho.findIndex(item => item.id === produto.id);
	if (idx >= 0) {
		carrinho[idx].qtd++;
	} else {
		carrinho.push({ ...produto, qtd: 1 });
	}
	atualizarContador();
	salvarCarrinho();
}

// Renderiza modal do carrinho
function mostrarCarrinho() {
	const modal = document.getElementById('cart-modal');
	if (carrinho.length === 0) {
		modal.innerHTML = '<div class="cart-empty">Carrinho vazio</div>';
	} else {
		modal.innerHTML = `
			<h2>Carrinho</h2>
			<ul>
				${carrinho.map((item, i) => `
					<li>
						${item.nome} (x${item.qtd}) - R$ ${(item.preco * item.qtd).toFixed(2)}
						<button data-rm="${i}" aria-label="Remover">Remover</button>
					</li>
				`).join('')}
			</ul>
			<div class="cart-total">Total: R$ ${carrinho.reduce((acc, item) => acc + item.preco * item.qtd, 0).toFixed(2)}</div>
			<button id="finalizar-btn">Finalizar Pedido</button>
			<button id="fechar-cart">Fechar</button>
		`;
	}
	modal.hidden = false;
}

// Fecha modal do carrinho
function fecharCarrinho() {
	document.getElementById('cart-modal').hidden = true;
}

// Remove item do carrinho
function removerItem(idx) {
	carrinho.splice(idx, 1);
	atualizarContador();
	salvarCarrinho();
	mostrarCarrinho();
}

// Envia pedido para o backend
async function finalizarPedido() {
	if (carrinho.length === 0) return;
	const res = await fetch(`${API_URL}/pedido`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ itens: carrinho })
	});
	if (res.ok) {
		alert('Pedido realizado com sucesso!');
		carrinho = [];
		atualizarContador();
		salvarCarrinho();
		fecharCarrinho();
		carregarProdutos();
	} else {
		alert('Erro ao finalizar pedido.');
	}
}

// Eventos globais
document.getElementById('cart-btn').onclick = mostrarCarrinho;
document.getElementById('cart-modal').onclick = function(e) {
	if (e.target.id === 'fechar-cart') fecharCarrinho();
	if (e.target.id === 'finalizar-btn') finalizarPedido();
	if (e.target.dataset.rm !== undefined) removerItem(Number(e.target.dataset.rm));
};

// Adiciona evento aos botões de adicionar ao carrinho
async function carregarProdutosComEventos() {
	await carregarProdutos();
	const lista = document.getElementById('product-list');
	Array.from(lista.querySelectorAll('button')).forEach((btn, i) => {
		btn.onclick = async () => {
			// Busca produtos novamente para garantir dados atualizados
			const res = await fetch(`${API_URL}/produtos`);
			const produtos = await res.json();
			const produto = produtos[i];
			adicionarAoCarrinho(produto);
		};
	});
}

window.addEventListener('DOMContentLoaded', () => {
	carregarCarrinho();
	carregarProdutosComEventos();
});
