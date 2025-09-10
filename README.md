# Loja Escolar

## Como executar

1. Instale as dependências do backend:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Gere os produtos de exemplo:
   ```bash
   python backend/seed.py
   ```
3. Inicie o backend:
   ```bash
   uvicorn backend.app:app --reload
   ```
4. Abra o arquivo `frontend/index.html` no navegador para visualizar o frontend.
