[English](README.md) | [中文](README.zh-CN.md)

# job-application

## 简介

`job-application` 是一个 Claude Code 插件，它把你过往简历所在的文件夹，转化为面向每一个
投递职位的定制申请材料。插件内置三个 skill —— `setup`、`apply`、`interview` —— 以及配套
的脚本、HTML 模板和子代理。`setup` 搭建工作目录，并（在给定过往简历文件夹时）构建事实来源；
`apply` 分析职位描述、生成定制简历与求职信并自检；`interview` 负责公司调研、问题准备和
模拟面试。插件本身是一个通用引擎：你的候选人数据保存在你自己的仓库里，绝不会随插件一起分发。

## 前置条件

- **Windows、macOS 或 Linux** —— 插件没有操作系统相关的依赖。
- **Python ≥ 3.10** 与 `pip`。安装引擎：`pip install jobkit`（在上架 PyPI 之前：
  `pip install "git+https://github.com/RyanDDDDDD/jobkit#subdirectory=plugins/job-application"`）。
  然后一次性运行 `jobkit install-browser`（下载由 Playwright 自行管理的 Chromium）。

不需要安装 Ghostscript、Poppler 或 `pandoc` —— PDF 压缩以及 `.pdf` / `.docx` 文本提取
均为纯 Python 实现（`pikepdf`、`pymupdf`、`python-docx`），随 `jobkit` 一起安装。

## 安装

将本仓库添加为插件市场并安装：

```
claude plugin marketplace add RyanDDDDDD/jobkit
claude plugin install job-application@job-application-marketplace
```

或将本地检出目录添加为市场（指向仓库根目录，而非本子目录）：

```
claude plugin marketplace add /path/to/jobkit
claude plugin install job-application@job-application-marketplace
```

### Cursor

同一仓库也是 Cursor 插件市场。在 Cursor 中：

```
Cursor → Settings → Plugins → Add marketplace → RyanDDDDDD/jobkit
```

然后安装 **job-application**。技能以 `/job-application:<skill>` 出现，
`jobkit` 引擎的安装方式相同（`pip install jobkit` + `jobkit install-browser`）。

## 初始设置

插件本身不存放任何候选人数据。它只从已安装的 `jobkit` 包（只读）读取自身资源，
**其余的一切 —— 你的事实来源和所有生成文档 —— 都在你运行 Claude Code 的那个目录里读写**，
由 `jobkit config` 向上查找 `jobapp.config.yml` 来确定。

1. 新建一个私有工作文件夹（例如 `~/job-hunt/`），在里面开 Claude Code。它要和本仓库分开，
   你生成的任何东西都不属于插件。
2. 运行 `/job-application:setup`。它会搭建这个文件夹 —— `jobapp.config.yml`、`CLAUDE.md`、
   一个包含 `resume_sections/` 模板和已播种 `interview_playbook.md` 的 `private/` 子目录，
   以及 `applications/` 输出目录。它绝不覆盖已存在的文件，可以放心重复运行。运行
   `/job-application:setup <你的过往简历文件夹>` 还可同时从这些简历构建
   `private/resume_sections/`。
3. 填写 `private/resume_sections/profile.yml`（身份、规范的公司名称／职位／日期）和
   `private/resume_sections/factual-bounds.md`（约束每一份生成文档的“绝不声称”规则）。
   若跳过了简历文件夹参数，可再带文件夹重跑 setup，或手动填写各个 section 文件
   （`companies/<slug>.md` / `projects/<slug>.md` 可从
   `templates/section-skeletons/` 下的骨架复制起步）。

`jobapp.config.yml` 的键 —— `source_of_truth_dir`、`output_dir`、`interview_playbook`、
`browser_path` —— 覆盖内置默认值（`resume_sections/`、`applications/{Company}/`、
`interview_playbook.md`）；`setup` 会把前三个写成 `private/` 布局。参见
`jobapp.config.example.yml`。

### 用内置样例试跑

在把插件对准你自己的数据之前，先用 `tests/fixtures/` 里的合成候选人跑一遍：
`/job-application:setup tests/fixtures/raw_cvs` 构建事实来源，然后对
`tests/fixtures/sample-jd.md` 运行 `/job-application:apply` 并把公司命名为 `Testco`
（样例 JD 是为虚构的 “Meridian Integration Partners” 写的，你把这份申请命名为
`Testco`）—— 你会得到虚构的 “Sample Dev” 的完整简历和求职信，并能从头到尾看到整条流水线。

`example/` 里只放这套输出渲染好的样例，仅四个 PDF —— 简历和求职信的中英两版
（`resume.pdf` / `resume.zh.pdf` / `cover_letter.pdf` / `cover_letter.zh.pdf`）。
渲染它们所用的 `*.data.json` 位于 `tests/fixtures/`。

## 日常使用

每个职位一轮：

```
/job-application:setup [<folder>]     # once: scaffold + build the source of truth
/job-application:apply [--density compact|standard] [--lang en|zh] [--answers "Q1; Q2"]
/job-application:interview research|prep|mock [behavioural|technical] [--lang en|zh]
```

- `/job-application:apply` 在一轮内完成分析 → 生成 → 自检，写出 `jd.md`、`analysis.md`、
  `review.md` 以及成品（`resume.pdf`、`cover_letter.pdf` / `cover_letter.txt`、可选的
  `answers.md`）。参数：`--density compact|standard` 设置简历行距密度（默认取自
  `profile.yml` `conventions.density`）；`--lang zh` 生成中文简历和求职信（正文由你的
  英文事实来源翻译而来）；`--answers "Q1; Q2"` 会额外写出 `answers.md`。当 JD 使项目
  相关时，Selected Projects 会自动加入。
- `/job-application:interview` 子命令：`research` 调度 `company-researcher` 子代理——它
  会先判断目标公司主要在国内还是海外招聘（或两者都有），据此选择搜索源（海外用
  Glassdoor/Seek/Indeed/LinkedIn；国内用 牛客网/脉脉/看准网/知乎/BOSS直聘）——写入
  `{dir}/interview/company_research.md`；`prep` 写出 `{dir}/interview/self_intro.md` 和
  `{dir}/interview/hr_questions_prep.md`；`mock behavioural|technical` 运行一场以简历为
  依据的模拟面试（行为面一轮，或逐个岗位、逐个项目的技术深挖），给出均衡的反馈，把带日期的
  记录写入 `{dir}/interview/mock/<mode>/<date>.md`（绝不覆盖——同一天再跑一次会得到
  `-2`、`-3`……），并把新出现的、反复出现的经验教训追加到面试 playbook（默认是工作目录
  根部的 `interview_playbook.md`；可用 `jobapp.config.yml` 中的 `interview_playbook`
  覆盖，例如 `private/interview_playbook.md`）。它首次使用时始终以英文的
  `jobkit doc interview-frameworks` 为种子。
  `mock technical` 还接受 `--focus "<岗位或项目>"`。`--lang en|zh` 设置这个子命令本次写出的
  一切内容的语言（研究报告、准备材料、模拟面试对话与记录、新增的 playbook 条目）；默认跟随
  这份申请 `apply` 时用的 `--lang`。

每个申请的文件都落在同一个目录里 —— 默认是 `applications/{Company}/`。可交给他人查看或
投递的成品与工作笔记平铺在根目录（`jd.md`、`analysis.md`、`review.md`、`resume.pdf`、
`cover_letter.pdf`、`cover_letter.txt`）；机器产物（`resume.data.json`、
`cover_letter.data.json`）放在 `tmp/` 下，可随时重新生成；面试准备文件放在 `interview/` 下
（模拟面试记录在 `interview/mock/<behavioural|technical>/<date>.md`）。完整目录树见
`jobkit doc output-layout`。可通过 `jobapp.config.yml` 中的 `output_dir` 覆盖该位置。

## 可选：Tavily 增强调研

`/job-application:interview research` 会从网上抓取公司文化、评价和面试反馈。
Glassdoor、Reddit 一类站点经常拦截普通抓取。配置 [Tavily](https://tavily.com)
API 密钥后，调研子代理改用 Tavily 的搜索与正文提取，通过率高得多。这完全是可选的
—— 没有密钥时调研仍走普通网页搜索，行为与以往完全一致。

1. 在 tavily.com 申请密钥（有免费额度）；形如 `tvly-…`。
2. 安装 Node（Tavily MCP 服务通过 `npx` 启动）。
3. **Claude Code：** 在启动 Claude Code 之前，于 shell 环境（或 Claude Code 的
   MCP 环境配置）中设置 `TAVILY_API_KEY`。
   **Cursor：** Settings → Plugins → job-application → Configure → 设置
   `TAVILY_API_KEY`。

国内调研（牛客网 / 脉脉 / 看准网 …）始终使用普通网页搜索 —— Tavily 帮不上忙。

## `resume_sections/` 约定

插件对你唯一的要求，是一个事实来源目录（默认 `resume_sections/`，可通过
`jobapp.config.yml` 覆盖）。它包含：

| 路径 | 用途 |
|------|---------|
| `profile.yml` | 结构化身份信息 —— 唯一的非 markdown 文件。姓名、联系方式、链接、所在地、工作权利，以及规范的岗位 / 教育经历（精确的公司名称、职位和日期，在每一份生成文档中逐字使用）。同时保存简历密度以及是否包含项目章节（`conventions.density` / `conventions.include_projects`）。 |
| `factual-bounds.md` | 自由格式的“绝不声称”规则，被 `apply` 作为硬约束逐字加载（例如你从未用过的技术、哪些技术栈属于哪个雇主、不编造指标、求职信中不提大学）。随着你修正生成的草稿而不断增长。 |
| `companies/*.md` | 整合、去重后的按公司划分的工作经历 —— 所有成就要点的事实来源。 |
| `projects/*.md` | 整合后的按项目划分的成就。 |
| `education.md` | 教育经历。 |
| `introduction.md` | 可复用的个人简介 / 定位陈述。 |
| `skills.md` | 整合后的技能清单。 |

`setup` 会搭建扁平文件（`profile.yml`、`factual-bounds.md`、`introduction.md`、
`skills.md`、`education.md`），并让 `companies/` 和 `projects/` 保持为空。每个新的
`companies/<slug>.md` / `projects/<slug>.md` 都从插件 `templates/section-skeletons/`
下的骨架起步 —— `setup` 在 CV 摄取时复制它，你手工填写时也可以自行复制。

## 运行测试

在 `plugins/job-application/` 目录下：

```
python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]" && python -m pytest
```

若尚未运行 `jobkit install-browser`，渲染相关检查会干净地跳过（不会失败）。

skill 的预期输出清单（`tests/skills/*.expected.md` —— `setup` / `apply` / `interview`）
所针对的合成候选人夹具位于 `tests/fixtures/`（`tests/fixtures/raw_cvs/`、
`tests/fixtures/resume_sections/`、`tests/fixtures/sample-jd.md`）。
