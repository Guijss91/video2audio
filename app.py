import streamlit as st
import subprocess
import tempfile
import requests
import os

# --- Configuração ---
# URL do seu webhook do n8n que recebe o áudio e retorna a transcrição
N8N_WEBHOOK_URL = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook-test/audio" 
# Substitua pela URL real do seu webhook, se for diferente.


# --- Interface do Usuário ---
st.set_page_config(layout="centered", page_title="Transcrição de Vídeo")
st.title("Extrair Áudio e Transcrever Vídeo")
st.write("Envie um vídeo para extrair o áudio, enviá-lo para transcrição e ver o resultado abaixo.")

# Inicializa o estado da sessão para armazenar a transcrição entre as execuções
if 'transcription_result' not in st.session_state:
    st.session_state.transcription_result = ""

# Componente de upload de arquivo
uploaded_file = st.file_uploader(
    "Selecione um arquivo de vídeo",
    type=["mp4", "mkv", "avi", "mov", "mpeg", "webm"]
)

# --- Lógica Principal ---
if uploaded_file is not None:
    st.video(uploaded_file)

    if st.button("▶️ Extrair Áudio e Transcrever"):
        # Limpa a transcrição anterior
        st.session_state.transcription_result = ""
        
        # Mostra um spinner durante o processamento
        with st.spinner('Aguarde... Extraindo áudio, enviando para o n8n e processando a transcrição...'):
            tmp_video_path = None
            tmp_audio_path = None
            try:
                # Salva o vídeo enviado em um arquivo temporário
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_video:
                    tmp_video.write(uploaded_file.getvalue())
                    tmp_video_path = tmp_video.name

                # Define o caminho para o arquivo de áudio de saída
                tmp_audio_path = os.path.splitext(tmp_video_path)[0] + ".mp3"

                # Comando FFmpeg para extrair o áudio (-y para sobrescrever o arquivo se existir)
                command = [
                    "ffmpeg", 
                    "-i", tmp_video_path, 
                    "-q:a", "0", 
                    "-map", "a", 
                    tmp_audio_path, 
                    "-y"
                ]
                
                # Executa o comando FFmpeg
                subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                st.info("Áudio extraído. Enviando para o serviço de transcrição...")

                # Envia o arquivo de áudio para o webhook do n8n
                with open(tmp_audio_path, "rb") as audio_file:
                    files = {
                        "file": (os.path.basename(tmp_audio_path), audio_file, "audio/mpeg")
                    }
                    # Adiciona o nome do arquivo original na requisição
                    data = {
                        "video_filename": uploaded_file.name
                    }
                    response = requests.post(N8N_WEBHOOK_URL, files=files, data=data, timeout=300) # Timeout de 5 minutos

                # Processa a resposta do n8n
                if response.status_code == 200:
                    transcription_data = response.json()
                    
                    # Verifica se a resposta é uma lista e contém dados
                    if transcription_data and isinstance(transcription_data, list):
                        result_data = transcription_data[0]
                        status = result_data.get('status')

                        if status == 'completed':
                            st.success("Transcrição concluída com sucesso!")
                            words = result_data.get('words')
                            
                            if words:
                                # Formata a transcrição com base nos interlocutores
                                formatted_text = ""
                                current_speaker = None
                                for word in words:
                                    speaker = word.get('speaker')
                                    if speaker != current_speaker:
                                        current_speaker = speaker
                                        if formatted_text:
                                            formatted_text += "\n\n"
                                        formatted_text += f"**Interlocutor {speaker}:** "
                                    formatted_text += word.get('text', '') + " "
                                st.session_state.transcription_result = formatted_text.strip()
                            else:
                                # Se 'words' for nulo ou vazio, usa o campo 'text'
                                full_text = result_data.get('text')
                                if full_text:
                                    st.session_state.transcription_result = full_text
                                else:
                                    st.warning("A transcrição foi concluída, mas não retornou um texto.")
                                    st.session_state.transcription_result = "Nenhum texto encontrado na resposta."

                        elif status in ['processing', 'queued']:
                            st.warning(f"O processo de transcrição ainda está em andamento (status: {status}). O resultado final será processado pelo n8n.")
                            st.session_state.transcription_result = f"Status da Transcrição: {status}."
                        
                        elif status == 'error':
                            st.error("Ocorreu um erro durante o processo de transcrição no serviço de destino.")
                            st.json(result_data)
                        
                        else:
                            st.warning(f"Status da transcrição desconhecido: '{status}'.")
                            st.json(result_data)
                    else:
                        st.warning("A resposta do n8n não está no formato esperado (lista JSON).")
                        st.json(transcription_data)

                else:
                    st.error(f"Erro ao chamar o webhook do n8n. Status: {response.status_code}")
                    st.text(response.text)

            except subprocess.CalledProcessError as e:
                st.error("Ocorreu um erro ao extrair o áudio com o FFmpeg.")
                st.code(e.stderr.decode('utf-8'))
            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão ao enviar o áudio: {e}")
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado: {e}")
            
            finally:
                # Limpa os arquivos temporários
                if tmp_video_path and os.path.exists(tmp_video_path):
                    os.remove(tmp_video_path)
                if tmp_audio_path and os.path.exists(tmp_audio_path):
                    os.remove(tmp_audio_path)

# Exibe a área de transcrição se houver resultado
if st.session_state.transcription_result:
    st.subheader("📝 Transcrição do Áudio")
    st.markdown(st.session_state.transcription_result)
    # Use st.text_area se preferir uma caixa de texto simples para copiar e colar
    # st.text_area("Resultado da Transcrição", st.session_state.transcription_result, height=300)

