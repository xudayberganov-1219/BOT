from flask import Flask, request, jsonify
import yt_dlp
import os
import requests

app = Flask(__name__)
os.makedirs("downloads", exist_ok=True)  # Fayllarni saqlash uchun papka

@app.route("/")
def home():
    return "VidDrop bot ishlayapti!"

@app.route("/download", methods=["POST"])
def download():
    try:
        data = request.get_json()
        url = data.get("url")
        if not url:
            return jsonify({"error": "URL topilmadi"}), 400

        ydl_opts = {
            'format': 'mp4',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Faylni file.io'ga yuklaymiz
        with open(filename, 'rb') as f:
            response = requests.post("https://file.io", files={"file": f})
            file_url = response.json().get("link")

        # Tizimdan faylni o‘chirish (ixtiyoriy)
        os.remove(filename)

        return jsonify({"file": file_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Railway uchun port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
