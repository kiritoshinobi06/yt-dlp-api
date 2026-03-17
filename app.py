from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import yt_dlp
import json
import random

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# User agents para rotar
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
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
            'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'no_check_certificate': True,
            'prefer_free_formats': False,
            'user_agent': random.choice(USER_AGENTS),
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'web', 'android', 'tv', 'mweb'],
                    'player_skip': ['webpage'],
                }
            },
            'socket_timeout': 30,
            'retries': 3,
            'http_chunk_size': '10M',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Obtener URL del video
            video_url = None
            
            if 'url' in info and info.get('protocol') in ['https', 'http', None]:
                video_url = info['url']
            
            if not video_url and 'formats' in info:
                for fmt in reversed(info.get('formats', [])):
                    if fmt.get('url') and fmt.get('protocol') in ['https', 'http', 'http_dash_segments', None]:
                        video_url = fmt['url']
                        break
            
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
        if 'Sign in' in error_msg or 'bot' in error_msg.lower() or 'confirm your age' in error_msg.lower():
            error_msg = 'YouTube requiere autenticación para este video.'
        elif 'Private video' in error_msg:
            error_msg = 'Este video es privado.'
        elif 'Unavailable' in error_msg or 'unavailable' in error_msg.lower():
            error_msg = 'Video no disponible.'
        elif 'format' in error_msg.lower():
            error_msg = 'Formato no disponible.'
        elif 'age' in error_msg.lower():
            error_msg = 'Video restringido por edad.'
        
        return jsonify({'status': 'error', 'text': error_msg}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'yt-dlp-api'})

# Handle OPTIONS preflight manualmente
@app.route('/', methods=['OPTIONS'])
def options_handler():
    response = make_response('', 200)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
