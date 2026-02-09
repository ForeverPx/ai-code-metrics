"""
Git AI 代码统计 - 独立 Web 应用
统计 GitLab 仓库中 AI 生成代码的占比（基于 refs/notes/ai）。
"""
from flask import Flask, send_from_directory
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from git_ai_stats import git_ai_stats_bp

app = Flask(__name__, static_folder='static', template_folder='templates')
app.register_blueprint(git_ai_stats_bp)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    print(f'Git AI 代码统计工具: http://{host}:{port}')
    app.run(debug=True, port=port, host=host)
