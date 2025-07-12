from flask import Flask, request, jsonify
import yt_dlp
import requests
import os

app = Flask(__name__)

@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get("url")

        # URL tekshiruvi
        if not url or not url.startswith("http"):
            return jsonify({"error": "Yaroqsiz URL"}), 400

        # Foyil nomi
        filename = "video.mp4"

        # Video yuklash
        ydl_opts = {
            'outtmpl': filename,
            'quiet': True,
            'format': 'mp4',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Faylni file.io ga yuklash
        with open(filename, 'rb') as f:
            response = requests.post('https://file.io', files={'file': f})

        if response.status_code == 200:
            file_url = response.json().get("link")
        else:
            return jsonify({"error": "Faylni yuklab bo‘lmadi"}), 500

        # Lokal faylni o‘chirish
        os.remove(filename)

        return jsonify({"file": file_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def home():
    return "Server ishlayapti", 200


@app.route('/health')
def health():
    return "OK", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
