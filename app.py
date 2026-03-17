from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import json
import random

app = Flask(__name__)
CORS(app)

# User agents para rotar y evitar detección
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]

@app.route('/', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'status': 'error', 'text': 'URL requerida'}), 400

        # Opciones optimizadas para evitar bloqueo
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'no_check_certificate': True,
            'user_agent': random.choice(USER_AGENTS),
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'web'],
                    'player_skip': ['webpage']
                }
            },
            'socket_timeout': 30,
            'retries': 3
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Obtener la URL directa del video
            video_url = None
            if 'url' in info:
                video_url = info['url']
            elif 'formats' in info and len(info['formats']) > 0:
                # Buscar el mejor formato con URL directa
                for fmt in reversed(info['formats']):
                    if 'url' in fmt and fmt.get('protocol') in ['https', 'http']:
                        video_url = fmt['url']
                        break
            
            if not video_url:
                return jsonify({
                    'status': 'error', 
                    'text': 'No se pudo obtener el enlace de descarga'
                }), 500

            result = {
                'status': 'success',
                'url': video_url,
                'title': info.get('title', 'Video'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0)
            }

            return jsonify(result)

    except Exception as e:
        error_msg = str(e)
        # Mejorar mensajes de error
        if 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower():
            error_msg = 'YouTube bloqueó la solicitud. Intenta con otro video o espera unos minutos.'
        elif 'Private video' in error_msg:
            error_msg = 'Este video es privado o no está disponible.'
        elif 'Unavailable' in error_msg:
            error_msg = 'Este video no está disponible.'
        
        return jsonify({'status': 'error', 'text': error_msg}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'yt-dlp-api'})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
