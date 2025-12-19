# Usa o Python leve
FROM python:3.11-slim

# Cria uma pasta dentro do servidor do Google
WORKDIR /app

# Copia a lista de bibliotecas e instala
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia suas pastas de código para o servidor
COPY backend/ backend/
COPY frontend/ frontend/

# Define a variável de ambiente para a porta
ENV PORT=8080

# Comando para iniciar o site
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080"]