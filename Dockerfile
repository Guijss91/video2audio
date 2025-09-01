# Imagem base leve
FROM python:3.11-slim

# Instala FFmpeg e dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
  && rm -rf /var/lib/apt/lists/*

# Cria diretório de trabalho
WORKDIR /app

# Copia dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia a aplicação
COPY app.py .

# Usuário não-root por segurança
RUN useradd -m appuser
USER appuser

# Porta padrão do Streamlit
EXPOSE 8501

# Comando para rodar o Streamlit em modo headless acessível externamente
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
