from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import json

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'status': 'error', 'text': 'URL requerida'}), 400
        
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            result = {
                'status': 'success',
                'url': info.get('url', info.get('formats', [{}])[-1].get('url')),
                'title': info.get('title', ''),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0)
            }
            
            return jsonify(result)
            
    except Exception as e:
        return jsonify({'status': 'error', 'text': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'yt-dlp-api'})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
