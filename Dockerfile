# Imagem base leve
FROM python:3.11-slim

# Variáveis de ambiente para Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Instala FFmpeg e dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Cria diretório de trabalho
WORKDIR /app

# Copia e instala dependências Python primeiro (para cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Cria estrutura de diretórios necessária
RUN mkdir -p templates static uploads logs

# Copia arquivos da aplicação
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Cria usuário não-root por segurança
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Muda para usuário não-root
USER appuser

# Porta padrão do Flask/Gunicorn
EXPOSE 5000

# Healthcheck para monitoramento
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Comando para rodar com Gunicorn em produção
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-", "app:app"]