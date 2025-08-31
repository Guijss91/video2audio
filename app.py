import streamlit as st
import subprocess
import tempfile
import requests
import os

# URLs do n8n
N8N_WEBHOOK_URL_AUDIO = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook/audio"
N8N_WEBHOOK_URL_TRANSCRICAO = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook/trancricao"

st.set_page_config(page_title="Transcrição Chat", layout="centered")
st.title("Extrair Áudio e Transcrever com AssemblyAI (via n8n)")

# Upload do vídeo
uploaded_file = st.file_uploader("Envie um vídeo", type=["mp4", "mkv", "avi", "mov"])

# Inicializar session_state para transcrição
if "utterances" not in st.session_state:
    st.session_state["utterances"] = []

if uploaded_file is not None:
    st.video(uploaded_file)

    if st.button("Extrair Áudio e Enviar"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_video.write(uploaded_file.read())
            tmp_video_path = tmp_video.name

        tmp_audio_path = tmp_video_path.replace(".mp4", ".mp3")

        try:
            subprocess.run([
                "ffmpeg", "-i", tmp_video_path, "-q:a", "0", "-map", "a", tmp_audio_path, "-y"
            ], check=True)
            st.success("Áudio extraído com sucesso!")

            with open(tmp_audio_path, "rb") as f:
                files = {"file": (os.path.basename(tmp_audio_path), f, "audio/mpeg")}
                data = {"video_filename": uploaded_file.name}
                response = requests.post(N8N_WEBHOOK_URL_AUDIO, files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                st.success("Áudio enviado e processado com sucesso!")

                # Guardar utterances no session_state
                utterances = result[0].get("utterances", [])
                if utterances:
                    st.session_state["utterances"] = utterances
                else:
                    st.warning("Nenhuma transcrição encontrada.")

            else:
                st.error(f"Erro ao enviar áudio: {response.status_code}")
                st.text(response.text)

        except Exception as e:
            st.error(f"Erro no processamento: {str(e)}")

        finally:
            if os.path.exists(tmp_video_path):
                os.remove(tmp_video_path)
            if os.path.exists(tmp_audio_path):
                os.remove(tmp_audio_path)

# Exibir chat se houver transcrição
if st.session_state["utterances"]:
    st.subheader("Transcrição (Chat)")
    utterances = st.session_state["utterances"]
    speakers = sorted(list({u['speaker'] for u in utterances}))
    colors = ["#f0f0f0", "#cce5ff", "#d1ffd1", "#ffd1d1", "#fff2cc", "#e0ccff", "#ffccf0"]
    speaker_colors = {sp: colors[i % len(colors)] for i, sp in enumerate(speakers)}

    for u in utterances:
        speaker = u['speaker']
        text = u['text']
        color = speaker_colors[speaker]
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-start; margin: 8px 0;">
                <div style="background-color: {color}; color: #000;
                            padding: 10px 15px; border-radius: 15px;
                            max-width: 70%; text-align: left;">
                    <b>{speaker}:</b> {text}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Botão para enviar transcrição final
    if st.button("Enviar transcrição final para n8n"):
        final_transcricao = [{"speaker": u['speaker'], "text": u['text']} for u in utterances]
        resp = requests.post(N8N_WEBHOOK_URL_TRANSCRICAO, json={"transcricao": final_transcricao})
        if resp.status_code == 200:
            st.success("Transcrição enviada com sucesso!")
        else:
            st.error(f"Erro ao enviar transcrição: {resp.status_code}")
            st.text(resp.text)
