import streamlit as st
import subprocess
import tempfile
import requests
import os

# URL do webhook do n8n (ajuste para o seu)
N8N_WEBHOOK_URL = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook-test/audio"

st.title("Remover Áudio de Vídeo e Enviar ao n8n")

# Upload do vídeo
uploaded_file = st.file_uploader("Envie um vídeo", type=["mp4", "mkv", "avi", "mov"])

if uploaded_file is not None:
    st.video(uploaded_file)

    if st.button("Extrair Áudio e Enviar"):
        # Salva o arquivo temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_video.write(uploaded_file.read())
            tmp_video_path = tmp_video.name

        # Caminho do arquivo de saída (áudio extraído)
        tmp_audio_path = tmp_video_path.replace(".mp4", ".mp3")

        # Extrair áudio usando ffmpeg
        try:
            subprocess.run([
                "ffmpeg", "-i", tmp_video_path, "-q:a", "0", "-map", "a", tmp_audio_path, "-y"
            ], check=True)

            st.success("Áudio extraído com sucesso!")

            # Enviar para webhook do n8n
            with open(tmp_audio_path, "rb") as f:
                files = {"file": (os.path.basename(tmp_audio_path), f, "audio/mpeg")}
                response = requests.post(N8N_WEBHOOK_URL, files=files)

            if response.status_code == 200:
                st.success("Áudio enviado com sucesso !")
                st.json(response.json())
            else:
                st.error(f"Erro ao enviar : {response.status_code}")
                st.text(response.text)

        except Exception as e:
            st.error(f"Erro no processamento: {str(e)}")

        # Limpeza opcional
        finally:
            if os.path.exists(tmp_video_path):
                os.remove(tmp_video_path)
            if os.path.exists(tmp_audio_path):
                os.remove(tmp_audio_path)
