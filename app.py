import streamlit as st
import subprocess
import tempfile
import requests
import os

# URLs do n8n
N8N_WEBHOOK_URL_AUDIO = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook/audio"
N8N_WEBHOOK_URL_TRANSCRICAO = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook/trancricao"

# Configuração da página com tema personalizado
st.set_page_config(
    page_title="Transcrição Chat", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🎬"
)

# CSS personalizado sem degradês
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
    
    :root {
        --primary-color: #4A90E2; /* Azul sólido */
        --secondary-color: #FF6B6B; /* Vermelho sólido */
        --background-color: #F5F7FA; /* Cinza claro */
        --card-bg: #FFFFFF;
        --text-primary: #2d3748;
        --text-secondary: #718096;
        --border-radius: 16px;
        --shadow: 0 6px 15px rgba(0, 0, 0, 0.08);
        --shadow-hover: 0 8px 20px rgba(0, 0, 0, 0.12);
    }
    
    .stApp {
        font-family: 'Inter', sans-serif;
        background: var(--background-color);
    }

    /* Header */
    .main-header {
        background: var(--card-bg);
        border-radius: var(--border-radius);
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: var(--shadow);
        text-align: center;
        border: 1px solid #e2e8f0;
    }

    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }

    .main-subtitle {
        color: var(--text-secondary);
        font-size: 1.1rem;
        font-weight: 400;
    }

    /* Cards */
    .card {
        background: var(--card-bg);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
        border: 1px solid #e2e8f0;
    }

    .card-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Upload area */
    .upload-area {
        border: 2px dashed var(--primary-color);
        border-radius: var(--border-radius);
        padding: 2rem;
        text-align: center;
        background: #f0f4ff;
        transition: all 0.3s ease;
        margin: 1rem 0;
    }

    .upload-area:hover {
        border-color: var(--secondary-color);
        background: #e6eeff;
    }

    /* Botões */
    .stButton > button {
        background: var(--primary-color) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 3px 10px rgba(74, 144, 226, 0.3) !important;
        min-height: 50px !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(74, 144, 226, 0.4) !important;
    }

    /* Barra lateral */
    section[data-testid="stSidebar"] {
        color: black !important; /* Força fonte preta */
    }

    /* Progress bar */
    .custom-progress {
        background: var(--primary-color);
        height: 6px;
        border-radius: 3px;
        animation: progress-animation 2s infinite;
    }

    @keyframes progress-animation {
        0% { width: 0%; }
        50% { width: 70%; }
        100% { width: 100%; }
    }

    /* Alertas */
    .custom-success {
        background: #38a169;
        color: white;
        padding: 1rem;
        border-radius: var(--border-radius);
        margin: 1rem 0;
        box-shadow: var(--shadow);
    }

    .custom-error {
        background: #e53e3e;
        color: white;
        padding: 1rem;
        border-radius: var(--border-radius);
        margin: 1rem 0;
        box-shadow: var(--shadow);
    }

    .custom-warning {
        background: #dd6b20;
        color: white;
        padding: 1rem;
        border-radius: var(--border-radius);
        margin: 1rem 0;
        box-shadow: var(--shadow);
    }

    /* Chat mensagens */
    .chat-message {
        margin: 12px 0;
        padding: 12px 18px;
        border-radius: 12px;
        max-width: 75%;
        background: var(--primary-color);
        color: white;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }

    /* Estatísticas */
    .stat-card {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        box-shadow: var(--shadow);
        border: 1px solid #e2e8f0;
        flex: 1;
        min-width: 120px;
    }

    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary-color);
    }

    .stat-label {
        font-size: 0.8rem;
        color: var(--text-secondary);
    }
</style>
""", unsafe_allow_html=True)
