from flask import Flask, render_template, request, jsonify, session
import subprocess
import tempfile
import requests
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'defensoria_publica_transcricao_2025'  # Altere para uma chave mais segura em produção

# URLs do n8n
N8N_WEBHOOK_URL_AUDIO = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook/audio"
N8N_WEBHOOK_URL_TRANSCRICAO = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook/trancricao"

# Configurações de upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mkv', 'avi', 'mov'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Criar pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video_file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo foi enviado'}), 400
    
    file = request.files['video_file']
    
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Formato de arquivo não suportado'}), 400
    
    # Verificar tamanho do arquivo
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': 'Arquivo muito grande. Máximo: 500MB'}), 400
    
    try:
        # Salvar arquivo temporário
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Extrair áudio
        audio_path = file_path.replace(os.path.splitext(file_path)[1], '.mp3')
        
        subprocess.run([
            "ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", audio_path, "-y"
        ], check=True)
        
        # Enviar para n8n
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
            data = {"video_filename": filename}
            response = requests.post(N8N_WEBHOOK_URL_AUDIO, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            utterances = result[0].get("utterances", [])
            
            if utterances:
                # Armazenar na sessão
                session['utterances'] = utterances
                session['video_filename'] = filename
                session['file_size'] = file_size
                
                return jsonify({
                    'success': True,
                    'message': 'Áudio processado com sucesso!',
                    'utterances': utterances,
                    'stats': {
                        'messages': len(utterances),
                        'speakers': len(set(u['speaker'] for u in utterances)),
                        'words': sum(len(u['text'].split()) for u in utterances)
                    }
                })
            else:
                return jsonify({'error': 'Nenhuma transcrição encontrada'}), 400
        else:
            return jsonify({'error': f'Erro no servidor: {response.status_code}'}), 500
            
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Erro ao extrair áudio do vídeo'}), 500
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500
    finally:
        # Limpar arquivos temporários
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)

@app.route('/send_transcription', methods=['POST'])
def send_transcription():
    if 'utterances' not in session:
        return jsonify({'error': 'Nenhuma transcrição disponível'}), 400
    
    try:
        utterances = session['utterances']
        final_transcricao = [{"speaker": u['speaker'], "text": u['text']} for u in utterances]
        
        response = requests.post(N8N_WEBHOOK_URL_TRANSCRICAO, json={"transcricao": final_transcricao})
        
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Transcrição enviada com sucesso!'})
        else:
            return jsonify({'error': f'Erro ao enviar transcrição: {response.status_code}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/clear_session', methods=['POST'])
def clear_session():
    session.clear()
    return jsonify({'success': True, 'message': 'Sessão limpa com sucesso!'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)