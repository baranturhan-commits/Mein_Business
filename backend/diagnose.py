
import os
import sys
import flask
import traceback
import subprocess

app = flask.Flask(__name__)

@app.route('/')
def index():
    return "<h1>Diagnose Server: ONLINE ✅</h1><p>Gehe zu <a href='/test_import'>/test_import</a> um den Crash-Fehler zu sehen.</p>"

@app.route('/health')
def health():
    return "online", 200

@app.route('/info')
def info():
    # Show Env (safe) and Packages
    env_str = "<br>".join([f"{k}: {v[:5]}..." if "KEY" in k else f"{k}: {v}" for k, v in os.environ.items()])
    try:
        pip_freeze = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode('utf-8').replace('\n', '<br>')
    except Exception as e:
        pip_freeze = str(e)
    
    return f"<h2>Environment</h2>{env_str}<h2>Packages</h2>{pip_freeze}"

@app.route('/test_import')
def test_import():
    try:
        # Versuch, die echte App zu importieren
        import api_server
        return f"<h1>Import SUCCESS!</h1><p>api_server konnte importiert werden. App Object: {api_server.app}</p>"
    except Exception:
        # Zeige den Fehler!
        error = traceback.format_exc()
        return f"<h1>Import FAILED! ❌</h1><pre>{error}</pre>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
