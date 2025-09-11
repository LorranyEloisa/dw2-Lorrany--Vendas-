

// Produtos mock de papelaria
const produtos = [
	{
		id: 1,
		nome: 'Caderno Universitário 96 folhas',
		preco: 18.90,
		estoque: 10,
		imagem: 'https://images.pexels.com/photos/4145195/pexels-photo-4145195.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 2,
		nome: 'Lápis Preto HB',
		preco: 1.50,
		estoque: 50,
		imagem: 'https://images.pexels.com/photos/159711/pencils-crayons-colorful-colour-159711.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 3,
		nome: 'Borracha Branca',
		preco: 2.00,
		estoque: 30,
		imagem: 'https://images.pexels.com/photos/159778/pexels-photo-159778.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 4,
		nome: 'Caneta Azul',
		preco: 2.50,
		estoque: 40,
		imagem: 'https://images.pexels.com/photos/356056/pexels-photo-356056.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 5,
		nome: 'Mochila Escolar',
		preco: 89.90,
		estoque: 8,
		imagem: 'https://images.pexels.com/photos/1027130/pexels-photo-1027130.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 6,
		nome: 'Estojo Simples',
		preco: 14.90,
		estoque: 15,
		imagem: 'https://images.pexels.com/photos/159776/pexels-photo-159776.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 7,
		nome: 'Régua 30cm',
		preco: 3.50,
		estoque: 25,
		imagem: 'https://images.pexels.com/photos/209679/pexels-photo-209679.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 8,
		nome: 'Apontador Duplo',
		preco: 2.80,
		estoque: 20,
		imagem: 'https://images.pexels.com/photos/159777/pexels-photo-159777.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 9,
		nome: 'Cola Branca 90g',
		preco: 4.50,
		estoque: 18,
		imagem: 'https://images.pexels.com/photos/159775/pexels-photo-159775.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 10,
		nome: 'Tesoura Escolar',
		preco: 6.90,
		estoque: 22,
		imagem: 'https://images.pexels.com/photos/159774/pexels-photo-159774.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 11,
		nome: 'Pasta Plástica com Elástico',
		preco: 5.90,
		estoque: 17,
		imagem: 'https://images.pexels.com/photos/159779/pexels-photo-159779.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 12,
		nome: 'Marca Texto Amarelo',
		preco: 3.90,
		estoque: 30,
		imagem: 'https://images.pexels.com/photos/51342/pexels-photo-51342.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 13,
		nome: 'Compasso Escolar',
		preco: 7.90,
		estoque: 10,
		imagem: 'https://images.pexels.com/photos/159780/pexels-photo-159780.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 14,
		nome: 'Bloco de Notas Adesivas',
		preco: 4.20,
		estoque: 25,
		imagem: 'https://images.pexels.com/photos/159781/pexels-photo-159781.jpeg?auto=compress&w=400&h=400&fit=crop'
	},
	{
		id: 15,
		nome: 'Corretivo Líquido',
		preco: 5.50,
		estoque: 12,
		imagem: 'https://images.pexels.com/photos/159782/pexels-photo-159782.jpeg?auto=compress&w=400&h=400&fit=crop'
	}
];

let carrinho = JSON.parse(localStorage.getItem('carrinho')) || [];

function salvarCarrinho() {
	localStorage.setItem('carrinho', JSON.stringify(carrinho));
}

function atualizarContadorCarrinho() {
	const count = carrinho.reduce((acc, item) => acc + item.qtd, 0);
	document.getElementById('cart-count').textContent = count;
}

function renderizarProdutos() {
	const lista = document.getElementById('product-list');
	lista.innerHTML = '';
	produtos.forEach(produto => {
		const card = document.createElement('div');
		card.className = 'card';
		card.innerHTML = `
			<img src="${produto.imagem}" alt="${produto.nome}">
			<div class="name">${produto.nome}</div>
			<div class="price">R$ ${produto.preco.toFixed(2)}</div>
			<div class="stock">${produto.estoque > 0 ? 'Em estoque' : 'Esgotado'}</div>
			<button ${produto.estoque === 0 ? 'disabled' : ''} aria-pressed="false" aria-label="Adicionar ao carrinho">Adicionar</button>
		`;
		const btn = card.querySelector('button');
		btn.addEventListener('click', () => adicionarAoCarrinho(produto));
		lista.appendChild(card);
	});
}

function carregarProdutos() {
	renderizarProdutos();
}

function adicionarAoCarrinho(produto) {
	const idx = carrinho.findIndex(item => item.id === produto.id);
	if (idx > -1) {
		if (carrinho[idx].qtd < produto.estoque) {
			carrinho[idx].qtd++;
		}
	} else {
		carrinho.push({ id: produto.id, nome: produto.nome, preco: produto.preco, qtd: 1 });
	}
	salvarCarrinho();
	atualizarContadorCarrinho();
	animarCarrinho();
}

function removerDoCarrinho(id) {
	carrinho = carrinho.filter(item => item.id !== id);
	salvarCarrinho();
	atualizarContadorCarrinho();
	renderizarCarrinho();
}

function alterarQtd(id, delta) {
	const item = carrinho.find(i => i.id === id);
	const prod = produtos.find(p => p.id === id);
	if (!item || !prod) return;
	if (item.qtd + delta > 0 && item.qtd + delta <= prod.estoque) {
		item.qtd += delta;
		salvarCarrinho();
		atualizarContadorCarrinho();
		renderizarCarrinho();
	}
}

function renderizarCarrinho() {
	const modal = document.getElementById('cart-modal');
	const itemsDiv = document.getElementById('cart-items');
	const totalDiv = document.getElementById('cart-total');
	if (carrinho.length === 0) {
		itemsDiv.innerHTML = '<p style="text-align:center;color:#888">Seu carrinho está vazio.</p>';
		totalDiv.textContent = '';
		document.getElementById('checkout-btn').disabled = true;
		return;
	}
	let total = 0;
	itemsDiv.innerHTML = '';
	carrinho.forEach(item => {
		const prod = produtos.find(p => p.id === item.id);
		const div = document.createElement('div');
		div.style.display = 'flex';
		div.style.justifyContent = 'space-between';
		div.style.alignItems = 'center';
		div.style.gap = '0.5rem';
		div.style.marginBottom = '0.5rem';
		div.innerHTML = `
			<span style="flex:1">${item.nome}</span>
			<button aria-label="Diminuir quantidade" style="width:28px">-</button>
			<span>${item.qtd}</span>
			<button aria-label="Aumentar quantidade" style="width:28px">+</button>
			<span>R$ ${(item.preco * item.qtd).toFixed(2)}</span>
			<button aria-label="Remover do carrinho" style="color:#EF4444;background:none;border:none;font-size:1.2rem">&times;</button>
		`;
		const [btnMenos, , , btnMais, , btnRemover] = div.querySelectorAll('button');
		btnMenos.addEventListener('click', () => alterarQtd(item.id, -1));
		btnMais.addEventListener('click', () => alterarQtd(item.id, 1));
		btnRemover.addEventListener('click', () => removerDoCarrinho(item.id));
		itemsDiv.appendChild(div);
		total += item.preco * item.qtd;
	});
	totalDiv.textContent = `Total: R$ ${total.toFixed(2)}`;
	document.getElementById('checkout-btn').disabled = false;
}

function abrirModalCarrinho() {
	document.getElementById('cart-modal').hidden = false;
	document.getElementById('modal-backdrop').hidden = false;
	renderizarCarrinho();
	// Foco acessível
	setTimeout(() => {
		document.querySelector('.close-modal').focus();
	}, 100);
	document.body.style.overflow = 'hidden';
}

function fecharModalCarrinho() {
	document.getElementById('cart-modal').hidden = true;
	document.getElementById('modal-backdrop').hidden = true;
	document.body.style.overflow = '';
}

function animarCarrinho() {
	const btn = document.getElementById('cart-btn');
	btn.style.transform = 'scale(1.15)';
	setTimeout(() => {
		btn.style.transform = '';
	}, 180);
}

function finalizarCompra() {
	alert('Compra finalizada! Obrigado.');
	carrinho = [];
	salvarCarrinho();
	atualizarContadorCarrinho();
	fecharModalCarrinho();
}

window.addEventListener('DOMContentLoaded', () => {
	console.log('JS carregado!');
	carregarProdutos();
	atualizarContadorCarrinho();
	// Modal
	document.getElementById('cart-btn').addEventListener('click', abrirModalCarrinho);
	document.getElementById('modal-backdrop').addEventListener('click', fecharModalCarrinho);
	document.querySelector('.close-modal').addEventListener('click', fecharModalCarrinho);
	document.getElementById('checkout-btn').addEventListener('click', finalizarCompra);
	// Fechar modal com ESC
	document.addEventListener('keydown', e => {
		if (!document.getElementById('cart-modal').hidden && e.key === 'Escape') fecharModalCarrinho();
	});
	// Forçar recarregamento dos produtos
	setTimeout(() => {
		carregarProdutos();
	}, 100);
});
