# Usando uma imagem leve do Python
FROM python:3.10-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Instalar dependências do sistema necessárias para o Postgres e compilação
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar os requisitos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Expor a porta padrão do Streamlit
EXPOSE 8501

# Comando para rodar a aplicação
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]