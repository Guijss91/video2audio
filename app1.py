import streamlit as st
import subprocess
import tempfile
import requests
import os

# URL do webhook do n8n (ajuste para o seu)
N8N_WEBHOOK_URL = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook-test/audio"

st.set_page_config(page_title="Transcrição AssemblyAI", layout="centered")
st.title("Extrair Áudio e Transcrever com AssemblyAI (via n8n)")

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

        try:
            # Extrair áudio com ffmpeg
            subprocess.run([
                "ffmpeg", "-i", tmp_video_path, "-q:a", "0", "-map", "a", tmp_audio_path, "-y"
            ], check=True)

            st.success("Áudio extraído com sucesso!")

            # Enviar para webhook do n8n
            with open(tmp_audio_path, "rb") as f:
                files = {"file": (os.path.basename(tmp_audio_path), f, "audio/mpeg")}
                data = {"video_filename": uploaded_file.name}
                response = requests.post(N8N_WEBHOOK_URL, files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                st.success("Áudio enviado e processado com sucesso!")

                # Mostra JSON bruto (debug)
                with st.expander("Ver JSON completo"):
                    st.json(result)

                if isinstance(result, list) and len(result) > 0:
                    job = result[0]
                    utterances = job.get("utterances", None)

                    if utterances:
                        st.subheader("Transcrição (Chat)")

                        # Identificar speakers únicos
                        speakers = sorted(list({u.get("speaker", "N/A") for u in utterances}))

                        # Opção de renomear speakers
                        speaker_map = {}
                        with st.expander("Renomear interlocutores"):
                            for sp in speakers:
                                new_name = st.text_input(f"Nome para {sp}", sp)
                                speaker_map[sp] = new_name if new_name.strip() else sp

                        # Estilo de chat
                        for u in utterances:
                            speaker = speaker_map.get(u.get("speaker", "N/A"), "N/A")
                            text = u.get("text", "")

                            if speaker == speakers[0]:
                                # Balão à esquerda
                                st.markdown(
                                    f"""
                                    <div style="display: flex; justify-content: flex-start; margin: 8px 0;">
                                        <div style="background-color: #f1f0f0; padding: 10px 15px; border-radius: 15px; max-width: 70%; text-align: left;">
                                            <b>{speaker}:</b> {text}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            else:
                                # Balão à direita
                                st.markdown(
                                    f"""
                                    <div style="display: flex; justify-content: flex-end; margin: 8px 0;">
                                        <div style="background-color: #d1e7dd; padding: 10px 15px; border-radius: 15px; max-width: 70%; text-align: left;">
                                            <b>{speaker}:</b> {text}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                    else:
                        st.warning("Nenhuma transcrição encontrada ainda.")
                else:
                    st.error("Resposta inesperada do n8n.")

            else:
                st.error(f"Erro ao enviar: {response.status_code}")
                st.text(response.text)

        except Exception as e:
            st.error(f"Erro no processamento: {str(e)}")

        finally:
            # Limpeza dos temporários
            if os.path.exists(tmp_video_path):
                os.remove(tmp_video_path)
            if os.path.exists(tmp_audio_path):
                os.remove(tmp_audio_path)
