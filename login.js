// login.js

document.getElementById('login-form').addEventListener('submit', function(e) {
  e.preventDefault();
  const usuario = document.getElementById('usuario').value;
  const senha = document.getElementById('senha').value;
  // Simples validação mock
  if (usuario === 'admin' && senha === '1234') {
    localStorage.setItem('usuarioLogado', 'admin');
    window.location.href = 'index.html';
  } else {
    document.getElementById('login-erro').textContent = 'Usuário ou senha inválidos!';
    document.getElementById('login-erro').style.display = 'block';
  }
});
