# omp-setup

个人 omp 配置、自写 wording skill 及其必需规则，不包含 secrets、凭据、会话或缓存。

## 安装

先安装 omp，然后克隆仓库并运行：

```bash
git clone https://github.com/wxdwfc/omp-setup.git
cd omp-setup
./install.sh
```

安装脚本通过 `omp config path` 获取当前配置目录，将其中的 `config.yml` 链接到本仓库的 `omp/config.yml`。如果当前使用的是 `config.yaml`，则保留该文件名。`OMP_PROFILE` 和 `PI_CODING_AGENT_DIR` 按 omp 自身规则生效。

同时将当前配置目录中的 `skills/wording` 链接到本仓库的 `omp/skills/wording`。已有 wording 目录或链接会完整备份到 `config-backup.XXXXXX/wording`，其他 skills 不受影响。

- 原文件或旧链接保存在配置目录下的 `config-backup.XXXXXX/` 中，安装时打印具体路径。
- 重复安装已经正确的链接不产生新备份。
- 不接管整个配置目录，不修改登录数据。
- 软链接使用绝对路径；移动仓库后重新运行 `./install.sh`。
- 换机器后，按需使用 `omp login` 重新登录。

## Wording

`modelRoles.wording` 只选择模型；实际工作流程由 `omp/skills/wording/SKILL.md` 提供。使用 `/skill:wording <文件或范围>` 启动逐条确认的 wording 检查；需要该模型时用 `omp --model @wording`。

`references/wording-rules.md` 随 skill 保存完整的保义约束和 wording 规则快照，来源记录在文件中。项目有 `third_party/agentic-research/` 时优先读取项目版本，否则使用随仓库安装的快照，不再依赖某台机器的绝对路径。

论文项目的 `PAPER.md`、其指定的 style skill 和范文仍是项目自身依赖，不复制到本仓库；缺失时 wording 工作流会明确报告。

## 日常修改

直接编辑 `omp/config.yml`，或在 omp 中使用 `/settings`、`omp config set`。omp 保存主配置时会保留软链接，更新仓库中的文件。

```bash
git diff -- omp/config.yml
git add omp/config.yml
git commit -m "Update omp preferences"
git push origin main
```

不自动提交或推送。不要把 token、API key 或密码写入此配置；Git 忽略规则不能阻止已跟踪文件中的敏感值进入提交。

`.gitignore` 使用白名单，只允许配置、安装脚本、本文档及已纳入的 wording 文件进入版本管理。新增其他文件时，需要显式调整白名单并检查内容。修改 wording 后，将对应的 `omp/skills/wording/` 文件一并 commit、push。

## 恢复原配置

在安装输出指定的备份目录中找到原配置。确认当前配置文件仍是本安装脚本创建的软链接，移除该链接，再将备份移回原路径。不要删除仓库中的 `omp/config.yml`；其他 omp 文件无需变动。

恢复旧 wording 时，先确认当前 `skills/wording` 是安装脚本创建的软链接，移除该链接，再把安装输出中的备份 `wording` 目录或旧链接移回 `skills/wording`。
