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

# CSS personalizado
st.markdown("""
<style>
    /* Importar Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
    
    /* Variáveis CSS */
    :root {
        --primary-color: #667eea;
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --secondary-color: #f093fb;
        --background-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --card-bg: rgba(255, 255, 255, 0.95);
        --text-primary: #2d3748;
        --text-secondary: #718096;
        --border-radius: 16px;
        --shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        --shadow-hover: 0 15px 35px rgba(0, 0, 0, 0.15);
    }
    
    /* Fonte global */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: var(--background-gradient);
    }
    
    /* Header principal */
    .main-header {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        border-radius: var(--border-radius);
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: var(--shadow);
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        animation: fadeInUp 0.8s ease;
    }
    
    .main-subtitle {
        color: var(--text-secondary);
        font-size: 1.1rem;
        font-weight: 400;
        animation: fadeInUp 0.8s ease 0.2s both;
    }
    
    /* Cards */
    .card {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
        animation: fadeInUp 0.6s ease;
    }
    
    .card:hover {
        box-shadow: var(--shadow-hover);
        transform: translateY(-2px);
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
        border: 2px dashed #667eea;
        border-radius: var(--border-radius);
        padding: 2rem;
        text-align: center;
        background: rgba(102, 126, 234, 0.05);
        transition: all 0.3s ease;
        margin: 1rem 0;
    }
    
    .upload-area:hover {
        border-color: #764ba2;
        background: rgba(102, 126, 234, 0.1);
        transform: scale(1.02);
    }
    
    /* Botões personalizados */
    .stButton > button {
        background: var(--primary-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        min-height: 50px !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* Progress bar personalizada */
    .custom-progress {
        background: linear-gradient(90deg, #667eea, #764ba2);
        height: 6px;
        border-radius: 3px;
        animation: progress-animation 2s infinite;
    }
    
    @keyframes progress-animation {
        0% { width: 0%; }
        50% { width: 70%; }
        100% { width: 100%; }
    }
    
    /* Chat container */
    .chat-container {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
        border: 1px solid rgba(255, 255, 255, 0.2);
        max-height: 500px;
        overflow-y: auto;
    }
    
    /* Mensagens do chat */
    .chat-message {
        margin: 12px 0;
        padding: 12px 18px;
        border-radius: 18px;
        max-width: 75%;
        animation: slideInLeft 0.4s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        position: relative;
    }
    
    .chat-message::before {
        content: '';
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        width: 0;
        height: 0;
    }
    
    .speaker-label {
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .message-text {
        line-height: 1.4;
        font-size: 0.95rem;
    }
    
    /* Sidebar */
    .sidebar-content {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Alertas personalizados */
    .custom-success {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        color: white;
        padding: 1rem;
        border-radius: var(--border-radius);
        margin: 1rem 0;
        box-shadow: var(--shadow);
        animation: slideInDown 0.5s ease;
    }
    
    .custom-error {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        color: white;
        padding: 1rem;
        border-radius: var(--border-radius);
        margin: 1rem 0;
        box-shadow: var(--shadow);
        animation: slideInDown 0.5s ease;
    }
    
    .custom-warning {
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        color: white;
        padding: 1rem;
        border-radius: var(--border-radius);
        margin: 1rem 0;
        box-shadow: var(--shadow);
        animation: slideInDown 0.5s ease;
    }
    
    /* Animações */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    /* Loading spinner */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Video container */
    .video-container {
        border-radius: var(--border-radius);
        overflow: hidden;
        box-shadow: var(--shadow);
        margin: 1rem 0;
        background: var(--card-bg);
        padding: 1rem;
    }
    
    /* Estatísticas */
    .stats-container {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
        flex-wrap: wrap;
    }
    
    .stat-card {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        box-shadow: var(--shadow);
        border: 1px solid rgba(255, 255, 255, 0.2);
        flex: 1;
        min-width: 120px;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-hover);
    }
    
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary-color);
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Remove margens padrão do Streamlit */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Scrollbar personalizada */
    .chat-container::-webkit-scrollbar {
        width: 6px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.1);
        border-radius: 3px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: var(--primary-gradient);
        border-radius: 3px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-color);
    }
</style>
""", unsafe_allow_html=True)

# Header principal com design melhorado
st.markdown("""
<div class="main-header">
    <div class="main-title">
        <i class="fas fa-video"></i> Transcrição Chat
    </div>
    <div class="main-subtitle">
        Extraia áudio de vídeos e gere transcrições inteligentes
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar com configurações e informações
with st.sidebar:
    st.markdown("""
    <div class="sidebar-content">
        <h3><i class="fas fa-cog"></i> Configurações</h3>
        <p>Configure as opções de processamento</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="sidebar-content">
        <h4><i class="fas fa-info-circle"></i> Formatos Suportados</h4>
        <ul>
            <li><i class="fas fa-file-video"></i> MP4</li>
            <li><i class="fas fa-file-video"></i> MKV</li>
            <li><i class="fas fa-file-video"></i> AVI</li>
            <li><i class="fas fa-file-video"></i> MOV</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="sidebar-content">
        <h4><i class="fas fa-chart-line"></i> Status do Sistema</h4>
        <p><i class="fas fa-circle" style="color: #48bb78;"></i> Servidor Online</p>
        <p><i class="fas fa-circle" style="color: #48bb78;"></i> API Disponível</p>
    </div>
    """, unsafe_allow_html=True)

# Layout principal com colunas
col1, col2 = st.columns([2, 1])

with col1:
    # Card de upload
    st.markdown("""
    <div class="card">
        <div class="card-title">
            <i class="fas fa-cloud-upload-alt"></i> Upload de Vídeo
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload do vídeo com área personalizada
    st.markdown('<div class="upload-area">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Arraste e solte seu vídeo aqui ou clique para selecionar", 
        type=["mp4", "mkv", "avi", "mov"],
        help="Tamanho máximo recomendado: 500MB"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    # Estatísticas do arquivo
    if uploaded_file is not None:
        st.markdown("""
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-value">{:.1f}</div>
                <div class="stat-label">MB</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{}</div>
                <div class="stat-label">Formato</div>
            </div>
        </div>
        """.format(
            len(uploaded_file.getvalue()) / (1024 * 1024),
            uploaded_file.name.split('.')[-1].upper()
        ), unsafe_allow_html=True)

# Inicializar session_state para transcrição
if "utterances" not in st.session_state:
    st.session_state["utterances"] = []

if uploaded_file is not None:
    # Video preview com container personalizado
    st.markdown('<div class="video-container">', unsafe_allow_html=True)
    st.markdown("""
    <div class="card-title">
        <i class="fas fa-play-circle"></i> Preview do Vídeo
    </div>
    """, unsafe_allow_html=True)
    st.video(uploaded_file)
    st.markdown('</div>', unsafe_allow_html=True)

    # Botão de processamento com design melhorado
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 Extrair Áudio e Enviar", use_container_width=True):
            # Progress bar personalizada
            progress_placeholder = st.empty()
            progress_placeholder.markdown("""
            <div class="card">
                <div class="card-title">
                    <i class="fas fa-cogs"></i> Processando...
                </div>
                <div class="custom-progress"></div>
                <p style="text-align: center; margin-top: 1rem;">
                    <span class="loading-spinner"></span> Extraindo áudio do vídeo...
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
                tmp_video.write(uploaded_file.read())
                tmp_video_path = tmp_video.name

            tmp_audio_path = tmp_video_path.replace(".mp4", ".mp3")

            try:
                # Atualizar progress
                progress_placeholder.markdown("""
                <div class="card">
                    <div class="card-title">
                        <i class="fas fa-cogs"></i> Processando...
                    </div>
                    <div class="custom-progress"></div>
                    <p style="text-align: center; margin-top: 1rem;">
                        <span class="loading-spinner"></span> Convertendo para áudio...
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                subprocess.run([
                    "ffmpeg", "-i", tmp_video_path, "-q:a", "0", "-map", "a", tmp_audio_path, "-y"
                ], check=True)
                
                # Sucesso personalizado
                progress_placeholder.markdown("""
                <div class="custom-success">
                    <i class="fas fa-check-circle"></i> Áudio extraído com sucesso!
                </div>
                """, unsafe_allow_html=True)

                # Atualizar para envio
                progress_placeholder.markdown("""
                <div class="card">
                    <div class="card-title">
                        <i class="fas fa-cloud-upload-alt"></i> Enviando...
                    </div>
                    <div class="custom-progress"></div>
                    <p style="text-align: center; margin-top: 1rem;">
                        <span class="loading-spinner"></span> Enviando para processamento...
                    </p>
                </div>
                """, unsafe_allow_html=True)

                with open(tmp_audio_path, "rb") as f:
                    files = {"file": (os.path.basename(tmp_audio_path), f, "audio/mpeg")}
                    data = {"video_filename": uploaded_file.name}
                    response = requests.post(N8N_WEBHOOK_URL_AUDIO, files=files, data=data)

                if response.status_code == 200:
                    result = response.json()
                    progress_placeholder.markdown("""
                    <div class="custom-success">
                        <i class="fas fa-check-circle"></i> Áudio enviado e processado com sucesso!
                    </div>
                    """, unsafe_allow_html=True)

                    # Guardar utterances no session_state
                    utterances = result[0].get("utterances", [])
                    if utterances:
                        st.session_state["utterances"] = utterances
                    else:
                        progress_placeholder.markdown("""
                        <div class="custom-warning">
                            <i class="fas fa-exclamation-triangle"></i> Nenhuma transcrição encontrada.
                        </div>
                        """, unsafe_allow_html=True)

                else:
                    progress_placeholder.markdown(f"""
                    <div class="custom-error">
                        <i class="fas fa-times-circle"></i> Erro ao enviar áudio: {response.status_code}
                    </div>
                    """, unsafe_allow_html=True)
                    st.text(response.text)

            except Exception as e:
                progress_placeholder.markdown(f"""
                <div class="custom-error">
                    <i class="fas fa-times-circle"></i> Erro no processamento: {str(e)}
                </div>
                """, unsafe_allow_html=True)

            finally:
                if os.path.exists(tmp_video_path):
                    os.remove(tmp_video_path)
                if os.path.exists(tmp_audio_path):
                    os.remove(tmp_audio_path)

# Exibir chat se houver transcrição
if st.session_state["utterances"]:
    st.markdown("""
    <div class="card">
        <div class="card-title">
            <i class="fas fa-comments"></i> Transcrição (Chat)
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    utterances = st.session_state["utterances"]
    speakers = sorted(list({u['speaker'] for u in utterances}))
    
    # Cores modernas para speakers
    colors = [
        "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
        "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
        "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)"
    ]
    speaker_colors = {sp: colors[i % len(colors)] for i, sp in enumerate(speakers)}
    
    # Estatísticas da conversa
    st.markdown(f"""
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-value">{len(utterances)}</div>
            <div class="stat-label">Mensagens</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(speakers)}</div>
            <div class="stat-label">Participantes</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{sum(len(u['text'].split()) for u in utterances)}</div>
            <div class="stat-label">Palavras</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Container do chat
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for i, u in enumerate(utterances):
        speaker = u['speaker']
        text = u['text']
        color = speaker_colors[speaker]
        
        # Ícone do speaker baseado no nome
        icon = "fas fa-user" if speaker == "SPEAKER_00" else "fas fa-user-tie" if speaker == "SPEAKER_01" else "fas fa-user-circle"
        
        st.markdown(
            f"""
            <div class="chat-message" style="background: {color}; color: white;">
                <div class="speaker-label">
                    <i class="{icon}"></i> {speaker}
                </div>
                <div class="message-text">{text}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Botão para enviar transcrição final com design melhorado
    col_final1, col_final2, col_final3 = st.columns([1, 2, 1])
    with col_final2:
        if st.button("🚀 Enviar para o SOLAR", use_container_width=True):
            # Loading state
            loading_placeholder = st.empty()
            loading_placeholder.markdown("""
            <div class="card">
                <div class="card-title">
                    <i class="fas fa-paper-plane"></i> Enviando...
                </div>
                <p style="text-align: center;">
                    <span class="loading-spinner"></span> Enviando transcrição para o SOLAR...
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            final_transcricao = [{"speaker": u['speaker'], "text": u['text']} for u in utterances]
            resp = requests.post(N8N_WEBHOOK_URL_TRANSCRICAO, json={"transcricao": final_transcricao})
            
            if resp.status_code == 200:
                loading_placeholder.markdown("""
                <div class="custom-success">
                    <i class="fas fa-check-circle"></i> Transcrição enviada com sucesso!
                </div>
                """, unsafe_allow_html=True)
            else:
                loading_placeholder.markdown(f"""
                <div class="custom-error">
                    <i class="fas fa-times-circle"></i> Erro ao enviar transcrição: {resp.status_code}
                </div>
                """, unsafe_allow_html=True)
                st.text(resp.text)

# Footer com informações adicionais
st.markdown("""
<div class="card" style="margin-top: 3rem; text-align: center;">
    <p style="color: var(--text-secondary); margin: 0;">
        <i class="fas fa-shield-alt"></i> Processamento seguro e confiável | 
        <i class="fas fa-clock"></i> Powered by FFmpeg + n8n
    </p>
</div>
""", unsafe_allow_html=True)