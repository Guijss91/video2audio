from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import subprocess
import tempfile
import requests
import os

app = Flask(__name__)
app.secret_key = "supersecret"  # Necessário para flash messages e session

# URLs do n8n
N8N_WEBHOOK_URL_AUDIO = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook/audio"
N8N_WEBHOOK_URL_TRANSCRICAO = "https://laboratorio-n8n.nu7ixt.easypanel.host/webhook/trancricao"

# Session local em memória (substitui st.session_state)
SESSION_STATE = {"utterances": []}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "video" not in request.files:
            flash("Nenhum arquivo enviado", "error")
            return redirect(url_for("index"))

        video_file = request.files["video"]

        if video_file.filename == "":
            flash("Arquivo inválido", "error")
            return redirect(url_for("index"))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            video_file.save(tmp_video.name)
            tmp_video_path = tmp_video.name

        tmp_audio_path = tmp_video_path.replace(".mp4", ".mp3")

        try:
            # Extrair áudio com ffmpeg
            subprocess.run(
                ["ffmpeg", "-i", tmp_video_path, "-q:a", "0", "-map", "a", tmp_audio_path, "-y"],
                check=True
            )

            # Enviar áudio para o n8n
            with open(tmp_audio_path, "rb") as f:
                files = {"file": (os.path.basename(tmp_audio_path), f, "audio/mpeg")}
                data = {"video_filename": video_file.filename}
                response = requests.post(N8N_WEBHOOK_URL_AUDIO, files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                utterances = result[0].get("utterances", [])
                SESSION_STATE["utterances"] = utterances
                flash("Áudio enviado e processado com sucesso!", "success")
            else:
                flash(f"Erro ao enviar áudio: {response.status_code}", "error")

        except Exception as e:
            flash(f"Erro no processamento: {str(e)}", "error")

        finally:
            if os.path.exists(tmp_video_path):
                os.remove(tmp_video_path)
            if os.path.exists(tmp_audio_path):
                os.remove(tmp_audio_path)

        return redirect(url_for("index"))

    return render_template("index.html", utterances=SESSION_STATE["utterances"])


@app.route("/enviar_transcricao", methods=["POST"])
def enviar_transcricao():
    utterances = SESSION_STATE.get("utterances", [])
    if not utterances:
        flash("Nenhuma transcrição disponível para envio", "warning")
        return redirect(url_for("index"))

    final_transcricao = [{"speaker": u["speaker"], "text": u["text"]} for u in utterances]
    resp = requests.post(N8N_WEBHOOK_URL_TRANSCRICAO, json={"transcricao": final_transcricao})

    if resp.status_code == 200:
        flash("Transcrição enviada com sucesso!", "success")
    else:
        flash(f"Erro ao enviar transcrição: {resp.status_code}", "error")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
