# omp-setup

个人 omp 配置、Research 自定义主题、自写 wording skill 及其必需规则、marketplace 插件清单，不包含 secrets、凭据、会话或缓存。

## 安装

先安装 omp、Git 和 jq（macOS 可用 `brew install jq`），然后克隆仓库并运行；首次安装插件需要联网：

```bash
git clone https://github.com/wxdwfc/omp-setup.git
cd omp-setup
./install.sh
```

安装脚本通过 `omp config path` 获取当前配置目录，将其中的 `config.yml` 链接到本仓库的 `omp/config.yml`。如果当前使用的是 `config.yaml`，则保留该文件名。`OMP_PROFILE` 和 `PI_CODING_AGENT_DIR` 按 omp 自身规则生效。

同时将当前配置目录中的 `skills/wording` 链接到本仓库的 `omp/skills/wording`。已有 wording 目录或链接会完整备份到 `config-backup.XXXXXX/wording`，其他 skills 不受影响。

主题按文件安装：将当前配置目录中的 `themes/research-night.json` 和 `themes/research-day.json` 分别链接到本仓库 `omp/themes/` 下的同名文件。已有文件或旧链接会逐个备份到 `config-backup.XXXXXX/`，其他主题不受影响；目标路径若是目录，脚本会拒绝替换。

- 原文件或旧链接保存在配置目录下的 `config-backup.XXXXXX/` 中，安装时打印具体路径。
- 重复安装已经正确的链接不产生新备份。
- 不接管整个配置目录，不修改登录数据。
- 软链接使用绝对路径；移动仓库后重新运行 `./install.sh`。
- 换机器后，按需使用 `omp login` 重新登录。

脚本还会按 `omp/plugins.txt` 注册 marketplace，并在当前 profile 的 user scope 安装缺失插件。已安装的插件直接跳过，不强制重装、不自动升级，也不改变禁用状态。

## Wording

`modelRoles.wording` 只选择模型；实际工作流程由 `omp/skills/wording/SKILL.md` 提供。使用 `/skill:wording <文件或范围>` 启动逐条确认的 wording 检查；需要该模型时用 `omp --model @wording`。

`references/wording-rules.md` 随 skill 保存完整的保义约束和 wording 规则快照，来源记录在文件中。项目有 `third_party/agentic-research/` 时优先读取项目版本，否则使用随仓库安装的快照，不再依赖某台机器的绝对路径。

论文项目的 `PAPER.md`、其指定的 style skill 和范文仍是项目自身依赖，不复制到本仓库；缺失时 wording 工作流会明确报告。

## Marketplace 插件

`omp/plugins.txt` 每行两列：marketplace 来源、`插件名@marketplace名称`；空行和以 `#` 开头的注释行会跳过。当前清单：

| 插件 | 来源 | 用途 |
| --- | --- | --- |
| `frontend-design@claude-plugins-official` | `anthropics/claude-plugins-official` | 前端设计指导 |

换机器或拉取清单更新后运行 `./install.sh`。清单同步的是安装意图，不固定插件版本；全新安装使用 marketplace 当前提供的版本。已有插件需要升级时，手动运行 `omp plugin marketplace update`，再运行 `omp plugin upgrade <插件名@marketplace名称>`。

安装失败时脚本返回非零状态；修复网络等问题后重新运行即可，已完成的安装会跳过。从清单删除一项不会卸载本机插件；卸载需显式运行 `omp plugin uninstall --scope user <插件名@marketplace名称>`。其他插件不受影响。

当前会话安装后执行 `/reload-plugins`，或重启 omp。

不要提交 `~/.omp/plugins/`、marketplace 缓存、安装状态中的绝对路径或 OAuth/API key。授权由 omp 在本机管理，仓库不复制凭据。

## 日常修改

直接编辑 `omp/config.yml`，或在 omp 中使用 `/settings`、`omp config set`。omp 保存主配置时会保留软链接，更新仓库中的文件。

状态栏右侧显示 `usage`（供应商额度）和 `context_pct`（上下文占用率）；Codex 订阅额度详情可在会话中用 `/usage` 查看，或运行 `omp usage --provider openai-codex`。

界面采用 Research 自定义主题：深色 `research-night`、浅色 `research-day`，搭配 Claude 风格输入框和透明状态栏，使用 `display.shimmer: classic`、隐藏 thinking。`symbolPreset: nerd` 使用 Nerd 图标，建议终端选择 JetBrains Mono Nerd Font；若图标显示为方框，可将其改回 `unicode`，不影响其他界面功能。本仓库不安装或修改终端字体。

子任务列表使用 `display.pinnedAgents: collapsed`，并启用 `display.subagentLivePreview`，显示各固定子任务当前或最近的工具调用。修改后重新启动 `omp` 体验；没有活动子任务时看不到实时预览效果。这套配置不依赖额外 UI 插件，也不安装通知扩展。

主题配色保存在 `omp/themes/research-night.json` 和 `omp/themes/research-day.json`。首次拉取主题文件或移动仓库后运行 `./install.sh` 建立链接；之后直接编辑这些文件即可，无需另行复制到本机配置目录。

```bash
git diff -- omp/config.yml omp/themes/
git add omp/config.yml omp/themes/
git commit -m "Update omp preferences"
git push origin main
```

不自动提交或推送。不要把 token、API key 或密码写入此配置；Git 忽略规则不能阻止已跟踪文件中的敏感值进入提交。

`.gitignore` 使用白名单，只允许主配置、两个 Research 主题文件、插件清单、安装脚本、说明、忽略规则、已纳入的 wording 文件和 `.github/workflows/secrets.yml` 进入版本管理。新增其他文件时，需要显式调整白名单并检查内容；新增主题还需更新 `install.sh` 的 `theme_files` 列表。修改 wording 或插件清单后，将对应的 `omp/skills/wording/` 或 `omp/plugins.txt` 文件一并 commit、push。

## Secret 扫描 CI

`.github/workflows/secrets.yml` 在每次 push、pull request 和手动触发时运行 [Gitleaks](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1)，扫描 checkout 拉取到的所有分支和标签的完整 Git 历史，包括当前检出的提交。发现疑似 secret 时，`Gitleaks` 检查失败；输出中的 secret 值完全脱敏，不上传扫描报告。

- 无需配置额外的 GitHub Secrets 或许可证。工作流仅授予 `contents: read`，checkout 不保留认证凭据。
- checkout 固定到 commit SHA；Gitleaks 固定到版本和发布包 SHA-256。升级时需同步更新对应的固定值。
- CI 在推送后才运行，无法阻止 secret 首次上传。若需阻止未通过扫描的 PR 合并，在 GitHub 分支保护或 ruleset 中将 `Gitleaks` 设置为必需检查。
- 命中真实凭据时，先撤销或轮换，再清理 Git 历史；仅从最新文件删除不足以让完整历史扫描通过。规则扫描无法保证发现所有类型的 secret。

本地安装 Gitleaks 后，可在推送前运行与 CI 相同的历史扫描：

```bash
gitleaks git --redact=100 --verbose --no-banner --log-opts="--all --full-history -m" .
```

此命令不检查尚未提交的修改；检查当前文件使用 `gitleaks dir --redact=100 .`。

## 恢复原配置

在安装输出指定的备份目录中找到原配置。确认当前配置文件仍是本安装脚本创建的软链接，移除该链接，再将备份移回原路径。不要删除仓库中的 `omp/config.yml`；其他 omp 文件无需变动。

恢复旧 wording 时，先确认当前 `skills/wording` 是安装脚本创建的软链接，移除该链接，再把安装输出中的备份 `wording` 目录或旧链接移回 `skills/wording`。

恢复旧主题时，先确认对应的 `themes/research-night.json` 或 `themes/research-day.json` 仍是本安装脚本创建的软链接，移除该链接，再把安装输出指定备份目录中的同名文件或旧链接移回原路径。两个主题分别备份，可能位于不同的 `config-backup.XXXXXX/` 目录中。
