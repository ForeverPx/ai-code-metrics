"""
Git AI 代码统计 - 后端逻辑
通过 GitLab API 获取 commits 与 refs/notes/ai，统计 AI 生成代码占比。
"""
from flask import Blueprint, request, jsonify
import requests
import json
import base64
from datetime import datetime
import os

git_ai_stats_bp = Blueprint('git_ai_stats', __name__, url_prefix='/git-ai-stats')

# 项目根目录（本文件所在目录即 new_project）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GITLAB_URL = os.getenv('GITLAB_BASE_URL', 'https://gitlab.com').rstrip('/')
GITLAB_TOKEN = os.getenv('GITLAB_PRIVATE_TOKEN', '')
REPOS_CONFIG_PATH = os.getenv('GIT_AI_REPOS_CONFIG', os.path.join(BASE_DIR, 'repos_config.json'))


def load_repos_config():
    """加载仓库配置（支持部门分组）"""
    config_path = REPOS_CONFIG_PATH
    print(f'[git_ai_stats] 📄 正在加载配置文件: {config_path}')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f'[git_ai_stats] ✅ 配置文件加载成功')

        if 'repos' in config:
            repos_count = len(config.get('repos', []))
            print(f'[git_ai_stats] 📦 配置中包含 {repos_count} 个仓库（旧格式）')
        else:
            total_repos = sum(len(repos) for repos in config.values() if isinstance(repos, list))
            departments = list(config.keys())
            print(f'[git_ai_stats] 📦 配置中包含 {len(departments)} 个部门，共 {total_repos} 个仓库（新格式）')
            for dept, repos in config.items():
                if isinstance(repos, list):
                    print(f'[git_ai_stats]    - {dept}: {len(repos)} 个仓库')

        return config
    except FileNotFoundError:
        print(f'[git_ai_stats] ❌ 配置文件不存在: {config_path}')
        return {}
    except json.JSONDecodeError as e:
        print(f'[git_ai_stats] ❌ 配置文件 JSON 格式错误: {e}')
        return {}
    except Exception as e:
        print(f'[git_ai_stats] ❌ 加载配置文件失败: {e}')
        import traceback
        traceback.print_exc()
        return {}


def get_departments_and_repos(config):
    """从配置中获取部门列表和仓库信息"""
    if 'repos' in config:
        return {
            "departments": [],
            "repos_by_department": {"默认": config.get('repos', [])},
            "all_repos": config.get('repos', [])
        }
    else:
        departments = [dept for dept in config.keys() if isinstance(config[dept], list)]
        repos_by_department = {dept: config[dept] for dept in departments}
        all_repos = []
        for repos in repos_by_department.values():
            all_repos.extend(repos)
        return {
            "departments": departments,
            "repos_by_department": repos_by_department,
            "all_repos": all_repos
        }


def filter_repos_by_departments(config, selected_departments):
    """根据选中的部门过滤仓库"""
    dept_info = get_departments_and_repos(config)
    if not selected_departments:
        return dept_info["all_repos"]
    filtered_repos = []
    for dept in selected_departments:
        if dept in dept_info["repos_by_department"]:
            filtered_repos.extend(dept_info["repos_by_department"][dept])
    return filtered_repos


def get_commits(project_id, ref_name, since, until):
    """获取指定时间范围内的所有 commits"""
    if not GITLAB_TOKEN:
        return []
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/commits"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    params = {
        "ref_name": ref_name,
        "since": since,
        "until": until,
        "with_stats": True,
        "per_page": 100
    }

    print(f'[git_ai_stats] ========== 开始获取 Commits ==========')
    print(f'[git_ai_stats] 项目ID: {project_id}, 分支: {ref_name}')
    print(f'[git_ai_stats] 时间范围: {since} ~ {until}')

    all_commits = []
    page = 1

    while True:
        params["page"] = page
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            commits = response.json()
            if not commits:
                break
            all_commits.extend(commits)
            if len(commits) < params["per_page"]:
                break
            page += 1
        except Exception as e:
            print(f'[git_ai_stats] ❌ 获取 commits 失败 (page {page}): {e}')
            break

    print(f'[git_ai_stats] Commits 获取完成，共 {len(all_commits)} 个')
    return all_commits


def get_commit_notes(project_id, commit_sha):
    """获取 commit 的 AI notes 信息 (refs/notes/ai)"""
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/files/{commit_sha}"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    params = {"ref": "refs/notes/ai"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()

        if "content" in data:
            content = base64.b64decode(data["content"]).decode('utf-8')
            if "---" in content:
                json_part = content.split("---", 1)[1].strip()
            else:
                json_part = content.strip()
            try:
                return json.loads(json_part)
            except json.JSONDecodeError:
                return None
        return None
    except Exception:
        return None


def calculate_ai_stats(repos, start_date, end_date):
    """计算所有仓库的 AI 代码统计"""
    total_lines = 0
    total_ai_lines = 0
    commits_with_ai = 0
    total_commits = 0
    repo_details = []

    since = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    until = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    for repo in repos:
        project_id = repo.get('id')
        repo_name = repo.get('name', 'unknown')
        branch = repo.get('branch', 'main')
        if not project_id:
            repo_details.append({
                'name': repo_name,
                'error': '缺少 project id，请配置 id 字段',
                'total_commits': 0,
                'total_lines': 0,
                'ai_lines': 0,
                'percentage': 0,
                'commit_details': []
            })
            continue

        print(f'[git_ai_stats] 处理仓库: {repo_name} (ID: {project_id}, Branch: {branch})')
        commits = get_commits(project_id, branch, since, until)

        repo_total_lines = 0
        repo_ai_lines = 0
        repo_commits_with_ai = 0
        commit_details = []

        for commit in commits:
            total_commits += 1
            commit_sha = commit['id']
            stats = commit.get('stats', {})
            additions = stats.get('additions', 0)
            repo_total_lines += additions

            notes = get_commit_notes(project_id, commit_sha)
            commit_ai_lines = 0
            if notes and 'prompts' in notes:
                for prompt_data in notes['prompts'].values():
                    accepted_lines = prompt_data.get('accepted_lines', 0)
                    commit_ai_lines += accepted_lines
                    repo_ai_lines += accepted_lines
                if commit_ai_lines > 0:
                    repo_commits_with_ai += 1

            # 保存每个commit的详细信息
            commit_details.append({
                'sha': commit_sha[:8],
                'short_sha': commit_sha[:8],
                'full_sha': commit_sha,
                'message': commit.get('message', '').split('\n')[0][:100],
                'author': commit.get('author_name', 'Unknown'),
                'date': commit.get('created_at', ''),
                'additions': additions,
                'ai_lines': commit_ai_lines,
                'percentage': round((commit_ai_lines / additions * 100) if additions > 0 else 0, 2)
            })

        total_lines += repo_total_lines
        total_ai_lines += repo_ai_lines
        commits_with_ai += repo_commits_with_ai

        repo_percentage = (repo_ai_lines / repo_total_lines * 100) if repo_total_lines > 0 else 0
        repo_details.append({
            'name': repo_name,
            'repo_name': repo_name,
            'total_lines': repo_total_lines,
            'ai_lines': repo_ai_lines,
            'percentage': round(repo_percentage, 2),
            'ratio_percent': round(repo_percentage, 2),
            'total_commits': len(commits),
            'commit_count': len(commits),
            'commits_with_ai': repo_commits_with_ai,
            'commit_details': commit_details
        })

    overall_percentage = (total_ai_lines / total_lines * 100) if total_lines > 0 else 0
    print(f'[git_ai_stats] 🎯 总体: 总行数={total_lines}, AI行数={total_ai_lines}, 占比={overall_percentage:.2f}%')

    return {
        'total_lines': total_lines,
        'total_ai_lines': total_ai_lines,
        'overall_percentage': round(overall_percentage, 2),
        'total_commits': total_commits,
        'commits_with_ai': commits_with_ai,
        'repo_details': repo_details
    }


@git_ai_stats_bp.route('/analyze', methods=['POST'])
def analyze():
    """分析 Git AI 代码占比"""
    try:
        data = request.get_json()
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        if not start_date_str or not end_date_str:
            return jsonify({'error': '请提供开始和结束日期'}), 400

        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))

        selected_departments = data.get('departments', [])
        config = load_repos_config()

        if selected_departments:
            repos = filter_repos_by_departments(config, selected_departments)
        else:
            dept_info = get_departments_and_repos(config)
            repos = dept_info["all_repos"]

        if not repos:
            return jsonify({'error': '未配置任何仓库或选中的部门没有仓库'}), 400

        stats = calculate_ai_stats(repos, start_date, end_date)
        return jsonify({'success': True, 'stats': stats})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'分析失败: {str(e)}'}), 500


@git_ai_stats_bp.route('/departments', methods=['GET'])
def get_departments():
    """获取部门列表"""
    try:
        config = load_repos_config()
        dept_info = get_departments_and_repos(config)
        return jsonify({
            'success': True,
            'departments': dept_info["departments"],
            'repos_by_department': dept_info["repos_by_department"]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@git_ai_stats_bp.route('/repos', methods=['GET'])
@git_ai_stats_bp.route('/repos-config', methods=['GET'])
def get_repos():
    """获取已配置的仓库列表（按部门分组）"""
    try:
        config = load_repos_config()
        dept_info = get_departments_and_repos(config)
        return jsonify({
            'success': True,
            'departments': dept_info["departments"],
            'repos_by_department': dept_info["repos_by_department"],
            'all_repos': dept_info["all_repos"]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
