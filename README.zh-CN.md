[English](README.md) | [中文](README.zh-CN.md)

# job-application

## 简介

`job-application` 是一个 Claude Code 插件，它把你过往简历所在的文件夹，转化为面向每一个
投递职位的定制申请材料。插件内置五个 skill —— `ingest`、`jd-intake`、`generate`、
`review-application`、`interview` —— 以及配套的脚本、HTML 模板和子代理。`ingest` 将你
历史上的简历整合为一个结构化的事实来源目录；`jd-intake` 对照该目录分析职位描述；
`generate` 生成一份定制的简历和求职信；`review-application` 对结果执行 QA 门禁；
`interview` 负责公司调研、问题准备和模拟面试。插件本身是一个通用引擎：你的候选人数据保存
在你自己的仓库里，绝不会随插件一起分发。

## 前置条件

- Windows，并安装 PowerShell 7（`pwsh`）。
- **一个 Chromium 内核浏览器** —— Microsoft Edge（Windows 预装）、Google Chrome 或
  Chromium —— 由 `scripts/render_pdf.ps1` 用来把 HTML 模板渲染为 PDF。会自动从
  Program Files / PATH 中检测，或在 `jobapp.config.yml` 中设置 `browser_path`。
- [Ghostscript](https://www.ghostscript.com/)（`gs` / `gswin64c` 在 PATH 上）——
  由 `scripts/compress_pdf.ps1` 用来压缩渲染出的 PDF。这一步需要 Ghostscript；完整安装的
  TinyTeX 也能满足，因为它捆绑了一个包装 Ghostscript 的 `ps2pdf`，脚本会将其作为回退方案。
- `pdftotext`（Poppler）—— `generate` 和 `review-application` 用它校验渲染出的 PDF 的
  文本，`ingest` 用它导入 `.pdf` 格式的源简历。
- 可选：`pandoc`，用于导入 `.docx` 格式的源简历。纯 `.tex` / `.md` 简历既不需要它，也不
  需要 `pdftotext`。
- 使用 `--lang zh` 时，需要系统安装一款 CJK 衬线字体（如 Noto Serif CJK / 思源宋体）——
  裸 Linux / CI 机器需要手动安装；Windows 和 macOS 自带。

## 安装

将本仓库添加为插件市场并安装：

```
claude plugin marketplace add <this repo>
claude plugin install job-application
```

或将本地检出目录添加为市场：

```
claude plugin marketplace add ./path/to/job-application
claude plugin install job-application
```

## 初始设置

1. 可选：如果你想使用非默认路径，把 `jobapp.config.example.yml` 复制为
   `jobapp.config.yml`（已被 git 忽略）—— `browser_path`、`ghostscript_path`、
   `source_of_truth_dir`、`output_dir`。跳过这一步则使用默认值
   （`resume_sections/`、`applications/{Company}/`）。
2. 运行 `/ingest <你的简历路径>`（指向存放过往简历的文件夹）来构建
   `resume_sections/`。
3. 检查 `resume_sections/profile.yml` —— 确认你的联系方式、规范的公司名称、职位名称和
   任职日期。
4. 检查 `resume_sections/factual-bounds.md` —— 约束每一份生成文档的“绝不声称”规则。

### 用内置样例试跑

在把插件对准你自己的数据之前，先用 `tests/fixtures/` 里的合成候选人跑一遍：
`/ingest tests/fixtures/raw_cvs` 构建事实来源，然后对 `tests/fixtures/sample-jd.md` 运行
`/jd-intake` 并把公司命名为 `Testco`（样例 JD 是为虚构的 “Meridian Integration Partners”
写的，你把这份申请命名为 `Testco`），再运行 `/generate` —— 你会得到虚构的 “Sample Dev” 的
完整简历和求职信，并能从头到尾看到整条流水线。

`example/` 里只放这套输出渲染好的样例，仅四个 PDF —— 简历和求职信的中英两版
（`resume.pdf` / `resume.zh.pdf` / `cover_letter.pdf` / `cover_letter.zh.pdf`）。
渲染它们所用的 `*.data.json` 位于 `tests/fixtures/`。

## 日常使用

每个职位一轮，按顺序执行：

```
/ingest <folder>                       # once (or after adding a new CV): build resume_sections/
/jd-intake                             # paste the job description, name the company
/generate [--density compact|standard] [--lang en|zh] [--with-projects]   # resume.data.json/pdf + cover_letter.data.json/pdf/txt
/review-application [--fix]            # QA gate: writes review.md (Pass / Flag / Fix)
/interview research|prep|mock          # company research | self-intro + HR prep | mock interview
```

- `/generate` 参数：`--density compact|standard` 设置简历的行距密度（默认取自
  `profile.yml`）；`--lang zh` 生成中文简历和求职信（正文由你的英文事实来源翻译而来）；
  `--with-projects` 加入一个由 JD 相关的 `projects/*.md` 构建的 Selected Projects 章节；
  `--max-pages N` 是一个软性页数上限（只发出警告，绝不截断内容）；
  `--order relevance|chronological` 设置工作经历的排序；`--answers "Q1; Q2"` 会额外写出
  `answers.md`。
- `/review-application --fix` 只应用明确且安全的更正（过往岗位里用现在时的要点、与
  `profile.yml` 不一致的字段、过时的 `cover_letter.txt`），重新渲染，并把各项检查再跑一次。
- `/interview` 子命令：`research` 调度 `company-researcher` 子代理写入
  `{dir}/company_research.md`；`prep` 写出 `{dir}/self_intro.md` 和
  `{dir}/hr_questions_prep.md`；`mock` 运行一场以简历为依据的模拟面试，给出均衡的反馈，并把
  新出现的、反复出现的经验教训追加到你仓库根目录的 `interview_playbook.md`（首次使用时
  以插件的 `interview-frameworks.md` 为种子）。

每个申请的文件都落在同一个目录里 —— 默认是 `applications/{Company}/`
（`jd.md`、`analysis.md`、`resume.data.json/pdf`、`cover_letter.data.json/pdf/txt`、
`review.md`，以及面试准备文件）。可通过 `jobapp.config.yml` 中的 `output_dir` 覆盖该位置。

## `resume_sections/` 约定

插件对你唯一的要求，是一个事实来源目录（默认 `resume_sections/`，可通过
`jobapp.config.yml` 覆盖）。它包含：

| 路径 | 用途 |
|------|---------|
| `profile.yml` | 结构化身份信息 —— 唯一的非 markdown 文件。姓名、联系方式、链接、所在地、工作权利，以及规范的岗位 / 教育经历（精确的公司名称、职位和日期，在每一份生成文档中逐字使用）。同时保存诸如默认简历长度、是否包含项目章节等约定。 |
| `factual-bounds.md` | 自由格式的“绝不声称”规则，被 `generate` 和 `review-application` 作为硬约束逐字加载（例如你从未用过的技术、哪些技术栈属于哪个雇主、不编造指标、求职信中不提大学）。随着你修正生成的草稿而不断增长。 |
| `companies/*.md` | 整合、去重后的按公司划分的工作经历 —— 所有成就要点的事实来源。 |
| `projects/*.md` | 整合后的按项目划分的成就。 |
| `education.md` | 教育经历。 |
| `introduction.md` | 可复用的个人简介 / 定位陈述。 |
| `skills.md` | 整合后的技能清单。 |

## 运行测试

所有机械性测试都从一个入口运行 —— 纯 PowerShell，不用 Pester：

```
pwsh tests/run-pipeline.ps1
```

它用 `tests/fixtures/*.data.json` 夹具渲染内置的 HTML 模板（断言简历为一页），运行
`cover_letter_to_txt.ps1` 和 `Get-JobAppConfig`，然后运行每个
`tests/scripts/*.Tests.ps1`，把它们的退出码折算进通过 / 失败计数。退出码 0 表示每一项检查
都通过。在没有 Chromium 浏览器的机器上，渲染相关的检查会干净地跳过。

skill 的预期输出清单（`tests/skills/*.expected.md`）所针对的合成候选人夹具位于
`tests/fixtures/`（`tests/fixtures/raw_cvs/`、`tests/fixtures/resume_sections/`、
`tests/fixtures/sample-jd.md`）。
