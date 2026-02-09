# Git AI 代码统计工具

团队用了 Cursor、Copilot 等 AI 写代码，但说不清「到底多少代码是 AI 写的」。本工具基于 [git-ai](https://github.com/git-ai-project/git-ai) 写入的 Git Notes（`refs/notes/ai`），从 GitLab 拉取提交与 AI 归属数据，按时间范围、仓库或部门统计 **AI 代码占比**，用一张表、一张图把结果摊开，方便做复盘、汇报和趋势观察。

**项目基于：[git-ai](https://github.com/git-ai-project/git-ai)**（追踪 AI 生成代码的 Git 扩展）及其 [Git AI Standard](https://github.com/git-ai-project/git-ai) 约定。

## 功能

- 按日期范围统计多仓库的 AI 代码占比
- 支持部门/分组配置，按组筛选仓库
- 总体统计 + 各仓库详情（行数、提交数、占比）
- 深色主题 Web 界面，日期选择、结果图表展示

## 环境要求

- Python 3.8+
- GitLab 实例（含 Git Notes `refs/notes/ai` 数据，如 Cursor / 其他 AI 编码工具写入的 AI 行数信息）

## 快速开始

### 1. 安装依赖

```bash
cd new_project
pip install -r requirements.txt
```

### 2. 配置环境变量

复制示例配置并填写 GitLab 令牌：

```bash
cp .env.example .env
# 编辑 .env，设置 GITLAB_PRIVATE_TOKEN
```

| 变量 | 必填 | 说明 |
|------|------|------|
| `GITLAB_PRIVATE_TOKEN` | 是 | GitLab Personal Access Token，需 `read_api`、`read_repository` |
| `GITLAB_BASE_URL` | 否 | GitLab 地址，默认 `https://gitlab.com` |
| `GIT_AI_REPOS_CONFIG` | 否 | 仓库配置 JSON 路径，默认项目根目录 `repos_config.json` |

### 3. 配置仓库列表

编辑 `repos_config.json`：

**简单格式（无分组）：**

```json
{
  "repos": [
    {
      "id": "123456",
      "name": "我的项目",
      "branch": "main"
    }
  ]
}
```

**按部门分组：**

```json
{
  "前端": [
    { "id": "111", "name": "web-app", "branch": "main" }
  ],
  "后端": [
    { "id": "222", "name": "api-server", "branch": "master" }
  ]
}
```

- `id`：GitLab 项目 ID（项目主页或 URL 中的 project id）
- `name`：展示名称
- `branch`：要统计的分支

### 4. 启动服务

```bash
python app.py
```

浏览器访问 **http://127.0.0.1:5000**，选择时间范围与部门（若有），点击「开始统计」即可。

## 工作原理

1. **Commits**：GitLab API 获取指定时间范围内各仓库、分支的提交列表及 `additions`/`deletions`。
2. **AI Notes**：对每个 commit 请求 `refs/notes/ai` 下的 Note 文件；若存在则解析其中的 JSON。
3. **统计**：汇总各 commit 的 `accepted_lines`（AI 接受行数）与 `additions`（总新增行数），计算占比。

AI 数据格式需与 Cursor 等工具写入的 Git Notes 一致（含 `prompts` 及每个 prompt 的 `accepted_lines` 等字段）。

## 项目结构

```
new_project/
├── app.py              # Flask 入口
├── git_ai_stats.py     # 统计与 API 逻辑
├── index.html          # 前端页面
├── repos_config.json  # 仓库配置（需自行配置）
├── requirements.txt
├── .env.example
└── README.md
```

## License

MIT
