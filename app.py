from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import json
import random

app = Flask(__name__)
CORS(app, origins=["*"], allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "OPTIONS"])

# User agents para rotar y evitar detección
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

@app.route('/', methods=['POST', 'OPTIONS'])
def download():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'status': 'error', 'text': 'URL requerida'}), 400

        # Opciones optimizadas
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'no_check_certificate': True,
            'user_agent': random.choice(USER_AGENTS),
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'web', 'android'],
                }
            },
            'socket_timeout': 30,
            'retries': 3
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Obtener URL del video
            video_url = None
            
            # Intentar 1: URL directa en info
            if 'url' in info and info.get('protocol') in ['https', 'http', None]:
                video_url = info['url']
            
            # Intentar 2: Buscar en formatos
            if not video_url and 'formats' in info:
                for fmt in reversed(info.get('formats', [])):
                    if fmt.get('url') and fmt.get('protocol') in ['https', 'http', 'http_dash_segments', None]:
                        video_url = fmt['url']
                        break
            
            # Intentar 3: Usar el primer formato disponible
            if not video_url and 'formats' in info and len(info['formats']) > 0:
                video_url = info['formats'][-1].get('url')

            if not video_url:
                return jsonify({
                    'status': 'error', 
                    'text': 'No se pudo obtener el enlace. Intenta con otro video.'
                }), 500

            result = {
                'status': 'success',
                'url': video_url,
                'title': info.get('title', 'Video')[:100],
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0)
            }

            return jsonify(result)

    except Exception as e:
        error_msg = str(e)
        if 'Sign in' in error_msg or 'bot' in error_msg.lower():
            error_msg = 'YouTube bloqueó la solicitud. Intenta con otro video.'
        elif 'Private video' in error_msg:
            error_msg = 'Este video es privado.'
        elif 'Unavailable' in error_msg:
            error_msg = 'Video no disponible.'
        elif 'format' in error_msg.lower():
            error_msg = 'Formato no disponible. Intenta con otro video.'
        
        return jsonify({'status': 'error', 'text': error_msg}), 500

@app.route('/health', methods=['GET'])
def health():
    response = jsonify({'status': 'ok', 'service': 'yt-dlp-api'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# CORS headers for all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
