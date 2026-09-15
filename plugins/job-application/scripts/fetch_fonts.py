"""One-shot helper: download Source Sans 3 (latin) + a lightweight Noto Sans SC
subset from Google Fonts into templates/fonts/. Not part of the runtime CLI."""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from urllib.parse import quote

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

OUT = Path(__file__).resolve().parents[1] / "src" / "jobkit" / "templates" / "fonts"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def source_sans3() -> None:
    css = get(
        "https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400..700&display=swap"
    ).decode()
    m = re.search(
        r"/\* latin \*/\s*@font-face \{[^}]+url\((https://[^)]+\.woff2)\)",
        css,
    )
    if not m:
        raise SystemExit("latin Source Sans 3 woff2 not found in CSS")
    data = get(m.group(1))
    path = OUT / "SourceSans3.woff2"
    path.write_bytes(data)
    print(f"wrote {path.name} ({len(data)} bytes)")


def noto_sans_sc_subset() -> None:
    common = (
        "的一是不了在人有我他这个们中来上大为和国地到以说时要就出会可也你对生能而子那得于着下自"
        "之年过发后作里用道行所然种事成方多经么去法学如都同现当没动面起看定天分还进好小部其些主"
        "样理心她本前开但因只从想实日军者意无力它与长把机十民第公此已工使情明性知全三又关点正"
        "业外将两高间由问很最重并物手应战向头文体政美相见被利等"
    )
    resume = (
        "简历求职信封面工作经历教育背景项目经验技能简介自我介绍技术栈性能调优架构重构服务"
        "集成持续交付自动化测试单元集成部署运维监控告警数据库关系型非关系型网络协议安全加密"
        "内存泄漏启动时间优化工程工业级组件瓶颈分析剖析确保零泄漏运行使用进行负责参与主导"
        "设计实现完成提升降低减少增加改进优化重构迁移接入对接联调上线发布灰度回滚容灾高可用"
        "负载均衡微服务分布式并发异步同步线程进程容器云原生虚拟化嵌入式驱动芯片固件编译链接"
        "调试性能剖析火焰图缓存队列消息中间件网关鉴权授权认证登录注册权限角色菜单接口文档"
        "需求评审迭代敏捷瀑布版本控制持续集成流水线制品仓库依赖管理代码审查静态检查动态分析"
        "单元覆盖率压测基准回归缺陷修复线上故障根因复盘文档规范协作沟通跨部门推动落地交付"
        "价值业务指标转化率留存活跃营收成本效率质量稳定性可靠性可扩展性可维护性可读性兼容性"
        "可移植性"
    )
    months = "一二三四五六七八九十零〇年月日至至今现任曾任"
    edu = (
        "本科硕士博士学士研究生学历学位专业计算机科学与技术软件工程电子信息通信工程人工智能"
        "自动化网络工程信息安全数据科学与大数据技术"
    )
    corp = "公司有限责任股份集团科技技术软件网络信息数据智能系统解决方案中心研究院实验室事业部"
    roles = "高级中级初级资深主任首席工程师开发程序员架构师技术经理主管总监实习生"
    punct = "，。：；！？、·｜—…（）【】「」《》\"\"''%+-/@#&*=<>"
    latin = (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        ".,:;!?()[]{}+-/\\@#%&*_\"'"
    )
    text = "".join(dict.fromkeys(common + resume + months + edu + corp + roles + punct + latin))
    print(f"subset unique chars: {len(text)}")

    css = get(
        "https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700"
        f"&display=swap&text={quote(text)}"
    ).decode()
    urls = re.findall(r"src: url\((https://[^)]+)\) format\('woff2'\)", css)
    if not urls:
        raise SystemExit(f"no Noto Sans SC woff2 urls; css head:\n{css[:400]}")

    names = ["NotoSansSC.woff2"]
    # Google may return one face per weight; keep the first (identical for text= subsets).
    data = get(urls[0])
    path = OUT / names[0]
    path.write_bytes(data)
    print(f"wrote {path.name} ({len(data)} bytes, magic={data[:4]!r})")
    if len(urls) > 1:
        print(f"(ignored {len(urls) - 1} extra weight face(s) from CSS)")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    source_sans3()
    noto_sans_sc_subset()
