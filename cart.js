// cart.js

function getCarrinho() {
  return JSON.parse(localStorage.getItem('carrinho')) || [];
}

function salvarCarrinho(carrinho) {
  localStorage.setItem('carrinho', JSON.stringify(carrinho));
}

function renderizarCarrinho() {
  const carrinho = getCarrinho();
  const itemsDiv = document.getElementById('cart-page-items');
  const totalDiv = document.getElementById('cart-page-total');
  if (carrinho.length === 0) {
    itemsDiv.innerHTML = '<p style="text-align:center;color:#888">Seu carrinho está vazio.</p>';
    totalDiv.textContent = '';
    return;
  }
  let total = 0;
  itemsDiv.innerHTML = '';
  carrinho.forEach(item => {
    const div = document.createElement('div');
    div.className = 'cart-item-row';
    div.innerHTML = `
      <span style="flex:1">${item.nome}</span>
      <span>Qtd: ${item.qtd}</span>
      <span>R$ ${(item.preco * item.qtd).toFixed(2)}</span>
      <button class="remover-btn">Remover</button>
    `;
    div.querySelector('.remover-btn').onclick = () => {
      removerDoCarrinho(item.id);
    };
    itemsDiv.appendChild(div);
    total += item.preco * item.qtd;
  });
  totalDiv.textContent = `Total: R$ ${total.toFixed(2)}`;
}

function removerDoCarrinho(id) {
  let carrinho = getCarrinho();
  carrinho = carrinho.filter(item => item.id !== id);
  salvarCarrinho(carrinho);
  renderizarCarrinho();
}

document.getElementById('pagamento-form').onsubmit = function(e) {
  e.preventDefault();
  localStorage.removeItem('carrinho');
  renderizarCarrinho();
  document.getElementById('pagamento-msg').textContent = 'Compra finalizada com sucesso!';
  document.getElementById('pagamento-msg').style.display = 'block';
};

renderizarCarrinho();
