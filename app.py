from flask import Flask, render_template, jsonify, request
import json

app = Flask(__name__)
API_SECRET = "0989320957" #設定您的專屬密碼
DB_FILE = "latest_signals.json"

@app.route('/')
def index():
    return render_template('index.html')
#manifest.json不需要實際存在這個個檔案
@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "台美股安全指數看板",
        "short_name": "股市看板",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#121212",
        "theme_color": "#0d6efd",
        "icons": [{"src": "/static/icon.png", "sizes": "192x192", "type": "image/png"}]
    })

@app.route('/api/update_signals', methods=['POST'])
def update_signals():
    # 檢查請求頭中的 Key 是否正確
    user_key = request.headers.get('X-API-KEY')
    if user_key != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)
    return jsonify({"status": "success"})

@app.route('/api/signals', methods=['GET'])
def get_signals():
    try:
        with open(DB_FILE, 'r') as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        # 檔案不存在時的預設 JSON 結構
        return jsonify({"date": "尚未更新", "has_signals": False, "signals": []})

if __name__ == '__main__':
    app.run()