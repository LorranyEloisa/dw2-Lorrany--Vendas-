// A11y: atalhos de teclado e foco
// Alt+N: novo produto (abre modal admin)
// Alt+C: abrir carrinho
document.addEventListener('keydown', (e) => {
	if (e.altKey && (e.key === 'n' || e.key === 'N')) {
		e.preventDefault();
		const btn = document.getElementById('admin-btn');
		if (btn) { btn.focus(); btn.click(); }
	}
	if (e.altKey && (e.key === 'c' || e.key === 'C')) {
		e.preventDefault();
		const btn = document.getElementById('cart-btn');
		if (btn) { btn.focus(); btn.click(); }
	}
});

// A11y: permitir fechar modal admin com Enter/Espaço no X
// A11y: garantir que o botão de fechar modal admin seja acessível por teclado
let adminCloseBtn = document.getElementById('admin-close');
if (adminCloseBtn) {
	adminCloseBtn.addEventListener('keydown', (e) => {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			adminCloseBtn.click();
		}
	});
}

// A11y: garantir que toast receba foco ao mostrar mensagem
function showToast(msg, color = '#22C55E') {
	const toast = document.getElementById('toast');
	toast.textContent = msg;
	toast.style.background = color;
	toast.hidden = false;
	toast.focus();
	setTimeout(() => { toast.hidden = true; }, 2500);
}
// Toast utilitário
function showToast(msg, color = '#22C55E') {
	const toast = document.getElementById('toast');
	toast.textContent = msg;
	toast.style.background = color;
	toast.hidden = false;
	setTimeout(() => { toast.hidden = true; }, 2500);
}
// --- CARRINHO LOCALSTORAGE ---
const CART_KEY = 'loja_escolar_cart';

function getCart() {
	return JSON.parse(localStorage.getItem(CART_KEY) || '[]');
}

function saveCart(cart) {
	localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

function addToCart(productId, qty = 1) {
	const products = window._productsCache || [];
	const prod = products.find(p => p.id === productId);
	if (!prod || prod.estoque === 0) return false;
	let cart = getCart();
	const idx = cart.findIndex(item => item.id === productId);
	if (idx >= 0) {
		if (cart[idx].qty + qty > prod.estoque) return false;
		cart[idx].qty += qty;
	} else {
		if (qty > prod.estoque) return false;
		cart.push({ id: productId, qty });
	}
	saveCart(cart);
	renderCartDrawer();
	return true;
}

function removeFromCart(productId) {
	let cart = getCart();
	cart = cart.filter(item => item.id !== productId);
	saveCart(cart);
	renderCartDrawer();
}

function updateQty(productId, qty) {
	const products = window._productsCache || [];
	const prod = products.find(p => p.id === productId);
	if (!prod) return;
	let cart = getCart();
	const idx = cart.findIndex(item => item.id === productId);
	if (idx >= 0) {
		if (qty < 1) qty = 1;
		if (qty > prod.estoque) qty = prod.estoque;
		cart[idx].qty = qty;
		saveCart(cart);
		renderCartDrawer();
	}
}

// --- DRAWER/MODAL DE CARRINHO ---
function renderCartDrawer() {
	const cart = getCart();
	const products = window._productsCache || [];
	const modal = document.getElementById('cart-modal');
	if (!modal) return;
	if (cart.length === 0) {
		modal.innerHTML = '<div class="cart-empty">Carrinho vazio</div>';
		modal.hidden = false;
		return;
	}
	let total = 0;
	let html = '<h2>Seu Carrinho</h2><ul>';
	cart.forEach(item => {
		const prod = products.find(p => p.id === item.id);
		if (!prod) return;
		const subtotal = prod.preco * item.qty;
		total += subtotal;
		html += `<li>
			<span>${prod.nome}</span>
			<input type='number' min='1' max='${prod.estoque}' value='${item.qty}' data-id='${prod.id}' class='cart-qty-input' style='width:48px'>
			x R$ ${prod.preco.toFixed(2)} = <b>R$ ${(subtotal).toFixed(2)}</b>
			<button data-remove='${prod.id}' aria-label='Remover'>&times;</button>
		</li>`;
	});
	html += '</ul>';
	html += `<div class='cart-total'>Total: <b>R$ ${total.toFixed(2)}</b></div>`;
	html += `<div class='cart-coupon'><input id='cart-coupon' maxlength='20' placeholder='Cupom de desconto'> <button id='cart-confirm-btn'>Finalizar Pedido</button></div>`;
	html += `<button id='fechar-cart'>Fechar</button>`;
	html += `<div id='cart-confirm-msg' style='margin-top:10px;'></div>`;
	modal.innerHTML = html;
	modal.hidden = false;

	// Eventos de quantidade
	modal.querySelectorAll('.cart-qty-input').forEach(input => {
		input.onchange = (e) => {
			const id = Number(e.target.dataset.id);
			let val = parseInt(e.target.value);
			if (isNaN(val) || val < 1) val = 1;
			updateQty(id, val);
		};
	});
	// Eventos de remover
	modal.querySelectorAll('button[data-remove]').forEach(btn => {
		btn.onclick = () => removeFromCart(Number(btn.dataset.remove));
	});
	// Fechar
	document.getElementById('fechar-cart').onclick = () => { modal.hidden = true; };

		// Finalizar pedido
		document.getElementById('cart-confirm-btn').onclick = async () => {
			const coupon = document.getElementById('cart-coupon').value.trim();
			const items = getCart().map(item => ({ produto_id: item.id, quantidade: item.qty }));
			const msgDiv = document.getElementById('cart-confirm-msg');
			msgDiv.textContent = 'Enviando pedido...';
			try {
				const res = await fetch(`${API_URL}/carrinho/confirmar`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ items, coupon: coupon || undefined })
				});
				const data = await res.json();
				if (!res.ok) throw new Error(data.detail || 'Erro ao finalizar pedido');
				saveCart([]);
				renderCartDrawer();
				fetchAndRenderProducts();
				modal.hidden = true;
				showToast(`Pedido #${data.order_id} confirmado! Total: R$ ${data.total_final.toFixed(2)}`);
			} catch (err) {
				msgDiv.textContent = err.message;
				showToast(err.message, '#EF4444');
			}
		};
}

// Substituir mostrarCarrinho para usar drawer
window.mostrarCarrinho = renderCartDrawer;

// --- ADMIN MODAL ---
const adminBtn = document.getElementById('admin-btn');
const adminModal = document.getElementById('admin-modal');
const adminClose = document.getElementById('admin-close');
const adminForm = document.getElementById('admin-form');
const adminErr = document.getElementById('admin-err');

adminBtn.onclick = () => {
	adminModal.hidden = false;
	adminForm.reset();
	adminErr.style.display = 'none';
};
adminClose.onclick = () => { adminModal.hidden = true; };
window.addEventListener('keydown', e => {
	if (!adminModal.hidden && e.key === 'Escape') adminModal.hidden = true;
});
adminModal.onclick = e => { if (e.target === adminModal) adminModal.hidden = true; };

adminForm.onsubmit = async (e) => {
	e.preventDefault();
	adminErr.style.display = 'none';
	// Validações
	const nome = adminForm['admin-nome'].value.trim();
	const descricao = adminForm['admin-desc'].value.trim();
	const preco = parseFloat(adminForm['admin-preco'].value);
	const estoque = parseInt(adminForm['admin-estoque'].value);
	const categoria = adminForm['admin-categoria'].value.trim();
	const sku = adminForm['admin-sku'].value.trim();
	if (!nome || nome.length < 2 || nome.length > 60) return showAdminErr('Nome obrigatório (2-60 caracteres)');
	if (descricao.length > 200) return showAdminErr('Descrição até 200 caracteres');
	if (isNaN(preco) || preco < 0.01) return showAdminErr('Preço deve ser >= 0.01');
	if (!Number.isInteger(estoque) || estoque < 0) return showAdminErr('Estoque deve ser inteiro >= 0');
	if (!categoria || categoria.length < 2 || categoria.length > 30) return showAdminErr('Categoria obrigatória (2-30 caracteres)');
	if (!sku || sku.length < 2 || sku.length > 20) return showAdminErr('SKU obrigatório (2-20 caracteres)');

	// Envio para backend
	try {
		const res = await fetch(`${API_URL}/produtos`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ nome, descricao, preco, estoque, categoria, sku })
		});
		if (!res.ok) {
			const data = await res.json().catch(() => ({}));
			throw new Error(data.detail || 'Erro ao salvar produto');
		}
		adminModal.hidden = true;
		fetchAndRenderProducts();
	} catch (err) {
		showAdminErr(err.message);
	}
};

function showAdminErr(msg) {
	adminErr.textContent = msg;
	adminErr.style.display = 'block';
}

const API_URL = 'http://localhost:8000';




// Função para renderizar os produtos no grid
function renderProducts(products) {
	window._productsCache = products;
	const grid = document.getElementById('product-list');
	grid.innerHTML = '';
	products.forEach(prod => {
		const card = document.createElement('div');
		card.className = 'product-card';
		card.innerHTML = `
			<img src="${prod.imagem || 'https://via.placeholder.com/120x120?text=Produto'}" alt="Imagem do produto" class="product-img">
			<div class="product-name">${prod.nome}</div>
			<div class="product-model">Modelo: <b>${prod.modelo || '-'}</b></div>
			<div class="product-desc">${prod.descricao || ''}</div>
			<div class="product-price">R$ ${Number(prod.preco).toFixed(2)}</div>
			<div class="product-stock">${prod.estoque > 0 ? `Estoque: ${prod.estoque}` : '<span class="out">Esgotado</span>'}</div>
			<button class="add-cart-btn" ${prod.estoque === 0 ? 'disabled' : ''}>Adicionar ao carrinho</button>
		`;
		// Adiciona evento ao botão
		card.querySelector('.add-cart-btn').onclick = (e) => {
			e.stopPropagation();
			if (!addToCart(prod.id, 1)) {
				card.classList.add('shake');
				setTimeout(() => card.classList.remove('shake'), 500);
			} else {
				animarAdicao(card);
			}
		};
		grid.appendChild(card);
	});
}



// --- ORDENACAO E PAGINACAO ---
const SORT_KEY = 'loja_escolar_sort';
const PAGE_SIZE = 10;
let currentPage = 1;
let totalPages = 1;

function getSortPref() {
	return localStorage.getItem(SORT_KEY) || 'nome_asc';
}
function setSortPref(val) {
	localStorage.setItem(SORT_KEY, val);
}

document.addEventListener('DOMContentLoaded', () => {
	const sortSel = document.getElementById('sort-select');
	if (sortSel) {
		sortSel.value = getSortPref();
		sortSel.onchange = (e) => {
			setSortPref(e.target.value);
			fetchAndRenderProducts(1);
		};
	}
});

function renderPagination() {
	const pag = document.getElementById('pagination-controls');
	if (!pag) return;
	pag.innerHTML = '';
	if (totalPages <= 1) return;
	const prev = document.createElement('button');
	prev.textContent = '<';
	prev.disabled = currentPage === 1;
	prev.onclick = () => fetchAndRenderProducts(currentPage - 1);
	pag.appendChild(prev);
	for (let i = 1; i <= totalPages; i++) {
		const btn = document.createElement('button');
		btn.textContent = i;
		btn.disabled = i === currentPage;
		btn.onclick = () => fetchAndRenderProducts(i);
		pag.appendChild(btn);
	}
	const next = document.createElement('button');
	next.textContent = '>';
	next.disabled = currentPage === totalPages;
	next.onclick = () => fetchAndRenderProducts(currentPage + 1);
	pag.appendChild(next);
}

// Buscar produtos da API e renderizar (com paginação e ordenação)
async function fetchAndRenderProducts(page = 1) {
	currentPage = page;
	const sort = getSortPref();
	let sortParam = '';
	if (sort === 'nome_asc') sortParam = 'nome_asc';
	else if (sort === 'nome_desc') sortParam = 'nome_desc';
	else if (sort === 'preco_asc') sortParam = 'preco_asc';
	else if (sort === 'preco_desc') sortParam = 'preco_desc';
	try {
		const res = await fetch(`${API_URL}/produtos?page=${page}&limit=${PAGE_SIZE}&sort=${sortParam}`);
		if (!res.ok) throw new Error('Erro ao buscar produtos');
		const data = await res.json();
		// Esperado: { items: [...], total: N }
		renderProducts(data.items);
		totalPages = Math.ceil((data.total || data.items.length) / PAGE_SIZE) || 1;
		renderPagination();
	} catch (err) {
		document.getElementById('product-list').innerHTML = '<div class="error">Erro ao carregar produtos.</div>';
		totalPages = 1;
		renderPagination();
	}
}

window.addEventListener('DOMContentLoaded', () => {
	carregarCarrinho();
	fetchAndRenderProducts(1);
});



// Animação de feedback ao adicionar ao carrinho
function animarAdicao(card) {
	card.classList.add('added');
	setTimeout(() => card.classList.remove('added'), 600);
}



// Filtros e busca (ajuste para usar fetchAndRenderProducts futuramente)
// function aplicarFiltros() {
//   const categoria = document.getElementById('filtro-categoria')?.value || '';
//   const sort = document.getElementById('filtro-ordenacao')?.value || '';
//   const search = document.getElementById('filtro-busca')?.value || '';
//   carregarProdutos({ categoria, sort, search });
// }

// window.addEventListener('DOMContentLoaded', () => {
//   carregarCarrinho();
//   carregarProdutos();
//   document.getElementById('filtro-categoria')?.addEventListener('change', aplicarFiltros);
//   document.getElementById('filtro-ordenacao')?.addEventListener('change', aplicarFiltros);
//   document.getElementById('btn-buscar')?.addEventListener('click', aplicarFiltros);
//   document.getElementById('filtro-busca')?.addEventListener('keydown', (e) => {
//     if (e.key === 'Enter') aplicarFiltros();
//   });
// });

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

// Carrega carrinho e produtos ao iniciar
window.addEventListener('DOMContentLoaded', () => {
	carregarCarrinho();
	carregarProdutos();
});
