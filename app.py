import streamlit as st
import subprocess
import tempfile
import requests
import os

# URLs do n8n
N8N_WEBHOOK_URL_AUDIO = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook-test/audio"
N8N_WEBHOOK_URL_TRANSCRICAO = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook-test/trancricao"

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

        tmp_audio_path = tmp_video_path.replace(".mp4", ".mp3")

        try:
            subprocess.run([
                "ffmpeg", "-i", tmp_video_path, "-q:a", "0", "-map", "a", tmp_audio_path, "-y"
            ], check=True)

            st.success("Áudio extraído com sucesso!")

            # Enviar para webhook do n8n
            with open(tmp_audio_path, "rb") as f:
                files = {"file": (os.path.basename(tmp_audio_path), f, "audio/mpeg")}
                data = {"video_filename": uploaded_file.name}
                response = requests.post(N8N_WEBHOOK_URL_AUDIO, files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                st.success("Áudio enviado e processado com sucesso!")

                with st.expander("Ver JSON completo"):
                    st.json(result)

                if isinstance(result, list) and len(result) > 0:
                    job = result[0]
                    utterances = job.get("utterances", None)

                    if utterances:
                        st.subheader("Transcrição (Chat)")

                        # Identificar speakers únicos
                        speakers = sorted(list({u.get("speaker", "N/A") for u in utterances}))

                        # Inicializar session_state para os nomes
                        if 'speaker_map' not in st.session_state:
                            st.session_state['speaker_map'] = {sp: sp for sp in speakers}

                        # Expander para renomear interlocutores
                        with st.expander("Renomear interlocutores"):
                            for sp in speakers:
                                new_name = st.text_input(f"Nome para {sp}", st.session_state['speaker_map'][sp], key=f"speaker_{sp}")
                                st.session_state['speaker_map'][sp] = new_name.strip() if new_name.strip() else sp

                        # Exibir balões de chat
                        for u in utterances:
                            speaker = st.session_state['speaker_map'].get(u.get("speaker", "N/A"), "N/A")
                            text = u.get("text", "")

                            if speaker == st.session_state['speaker_map'][speakers[0]]:
                                # Balão à esquerda (cinza)
                                st.markdown(
                                    f"""
                                    <div style="display: flex; justify-content: flex-start; margin: 8px 0;">
                                        <div style="background-color: #f0f0f0; color: #000; 
                                                    padding: 10px 15px; border-radius: 15px; 
                                                    max-width: 70%; text-align: left;">
                                            <b>{speaker}:</b> {text}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            else:
                                # Balão à direita (azul)
                                st.markdown(
                                    f"""
                                    <div style="display: flex; justify-content: flex-end; margin: 8px 0;">
                                        <div style="background-color: #cce5ff; color: #000; 
                                                    padding: 10px 15px; border-radius: 15px; 
                                                    max-width: 70%; text-align: left;">
                                            <b>{speaker}:</b> {text}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                        # Botão para enviar transcrição final
                        if st.button("Enviar transcrição final para o n8n"):
                            final_transcricao = [
                                {"speaker": st.session_state['speaker_map'].get(u.get("speaker", "N/A"), "N/A"),
                                 "text": u.get("text", "")}
                                for u in utterances
                            ]

                            resp = requests.post(
                                N8N_WEBHOOK_URL_TRANSCRICAO,
                                json={"transcricao": final_transcricao}
                            )

                            if resp.status_code == 200:
                                st.success("Transcrição enviada com sucesso ao n8n!")
                            else:
                                st.error(f"Erro ao enviar transcrição: {resp.status_code}")
                                st.text(resp.text)
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
            if os.path.exists(tmp_video_path):
                os.remove(tmp_video_path)
            if os.path.exists(tmp_audio_path):
                os.remove(tmp_audio_path)
