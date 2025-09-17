

// Produtos mock de papelaria
const produtos = [
  {
    id: 1,
    nome: "Lápis",
    preco: 2.50,
    estoque: 100,
    imagem: "https://images.tcdn.com.br/img/img_prod/1315861/lapis_desenho_6b_madeira_kz3623_788_1_f1fd3aba1ad7b25a6ef4966f6573c9c8.jpg"
  },
  
{
  id: 2,
  nome: "Caderno",
  preco: 15.00,
  estoque: 50,
  imagem: "https://images.tcdn.com.br/img/img_prod/977007/caderno_universitario_1_materia_96_folhas_azul_2031_1_20201204155354.jpg"
  },
  {
    id: 3,
    nome: "Borracha",
    preco: 3.00,
    estoque: 80,
    imagem: "https://fotos.oceanob2b.com/High/043190.jpg"
  },
  {
    id: 4,
    nome: "Régua",
    preco: 4.50,
    estoque: 60,
    imagem: "https://bazarhorizonte.vtexassets.com/arquivos/ids/391124/009857_000000_2.jpg?v=637904800487470000"
  },
  {
    id: 5,
    nome: "Mochila",
    preco: 75.00,
    estoque: 30,
    imagem: "https://images.tcdn.com.br/img/img_prod/1243909/mochila_escolar_de_costas_packn_go_309_1_08cdda36e1b156311c3007d685154d5f.jpg"
  },
  {
    id: 6,
    nome: "Apontador",
    preco: 2.00,
    estoque: 70,
    imagem: "https://www.faber-castell.com.br/-/media/Products/Product-Repository/Miscellaneous-sharpeners/24-24-21-Sharpener/588513-Sharpener-Classical-Mix/Images/588513_10_PM1.ashx?bc=ffffff&as=0&h=900&w=900&sc_lang=pt-BR&hash=1FFFE16169A011D231B18A8D7B25992F"
  },
  {
    id: 7,
    nome: "Cola",
    preco: 5.00,
    estoque: 40,
    imagem: "https://www.tilibra.com.br/storage/products/md/cola-branca-120g-lavavel_345563-e1.jpg?c=88f51d10807abf8d5f0097c252673442"
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
