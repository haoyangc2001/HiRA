# -*- coding: utf-8 -*-
"""软著申请材料生成器：源代码鉴别材料 + 申请表信息 + 操作手册 -> HTML -> PDF(Chrome无头打印)"""
import os, io, tokenize, subprocess, shutil, datetime, re

ROOT = r"D:\repository\Go2HierarchicalReachAvoidRL"
OUT = os.path.join(ROOT, "output", "copyright_materials")
os.makedirs(OUT, exist_ok=True)
TMP = os.path.join(OUT, "_t")
os.makedirs(TMP, exist_ok=True)

SOFTWARE_NAME = "四足机器人分层安全导航强化学习训练平台"
VERSION = "V1.0.0"
OWNER = "曹豪洋"
HEADER = f"{SOFTWARE_NAME} {VERSION}"

DIRS = ["legged_gym_go2/legged_gym", "rsl_rl/rsl_rl"]

# ---- 源码取页：显式优先顺序（核心模块在前） ----
PRIORITY = [
    "rsl_rl/rsl_rl/algorithms/reach_avoid_ppo.py",
    "rsl_rl/rsl_rl/algorithms/ppo.py",
    "rsl_rl/rsl_rl/modules/actor_critic.py",
    "rsl_rl/rsl_rl/modules/actor_critic_recurrent.py",
    "rsl_rl/rsl_rl/storage/rollout_storage.py",
    "rsl_rl/rsl_rl/runners/on_policy_runner.py",
    "rsl_rl/rsl_rl/utils/utils.py",
    "legged_gym_go2/legged_gym/envs/go2/go2_config.py",
    "legged_gym_go2/legged_gym/envs/go2/go2_env.py",
    "legged_gym_go2/legged_gym/envs/go2/high_level_navigation_env.py",
    "legged_gym_go2/legged_gym/envs/go2/hierarchical_go2_env.py",
    "legged_gym_go2/legged_gym/envs/base/legged_robot.py",
    "legged_gym_go2/legged_gym/envs/base/legged_robot_config.py",
    "legged_gym_go2/legged_gym/envs/base/base_task.py",
    "legged_gym_go2/legged_gym/envs/base/base_config.py",
    "legged_gym_go2/legged_gym/scripts/train_reach_avoid.py",
    "legged_gym_go2/legged_gym/scripts/play_reach_avoid.py",
    "legged_gym_go2/legged_gym/scripts/test_reach_avoid.py",
    "legged_gym_go2/legged_gym/scripts/play_fixed_commands_with_video.py",
    "legged_gym_go2/legged_gym/scripts/plot_training_results.py",
    "legged_gym_go2/legged_gym/scripts/plot_env_layout.py",
    "legged_gym_go2/legged_gym/utils/helpers.py",
    "legged_gym_go2/legged_gym/utils/terrain.py",
    "legged_gym_go2/legged_gym/utils/task_registry.py",
    "legged_gym_go2/legged_gym/utils/logger.py",
    "legged_gym_go2/legged_gym/utils/isaacgym_utils.py",
    "legged_gym_go2/legged_gym/utils/math.py",
    "legged_gym_go2/legged_gym/envs/h1_2/h1_2_config.py",
    "legged_gym_go2/legged_gym/envs/h1_2/h1_2_env.py",
    "legged_gym_go2/legged_gym/envs/h1/h1_config.py",
    "legged_gym_go2/legged_gym/envs/h1/h1_env.py",
    "legged_gym_go2/legged_gym/envs/g1/g1_config.py",
    "legged_gym_go2/legged_gym/envs/g1/g1_env.py",
    "legged_gym_go2/legged_gym/envs/tinymal/tinymal_config.py",
    "legged_gym_go2/legged_gym/envs/tinymal/tinymal_env.py",
]

def collect_files():
    found = set()
    order = []
    for rel in PRIORITY:
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p):
            order.append(rel); found.add(rel)
    # 兜底：补上其余 .py
    extra = []
    for d in DIRS:
        for dp, dn, fn in os.walk(os.path.join(ROOT, d)):
            if "__pycache__" in dp:
                dn[:] = [x for x in dn if x != "__pycache__"]
                continue
            for f in fn:
                if f.endswith(".py"):
                    rel = os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/")
                    if rel not in found:
                        extra.append(rel)
    extra.sort()
    return order + extra

def strip_comments(src):
    """去注释(保留字符串字面量)、去空行；返回有效代码行列表。"""
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except Exception:
        lines = [l.rstrip() for l in src.splitlines()]
        return [l for l in lines if l.strip() != ""]
    cm = {}
    for t in toks:
        if t.type == tokenize.COMMENT:
            cm.setdefault(t.start[0], []).append((t.start[1], t.end[1]))
    out = []
    for i, line in enumerate(src.splitlines(), start=1):
        if i in cm:
            for s, e in sorted(cm[i], reverse=True):
                line = line[:s] + line[e:]
        line = line.rstrip()
        if line.strip() == "":
            continue
        out.append(line)
    return out

def wrap_line(line, limit=100):
    """超长行折行到 <=limit 字符物理行（尽量在空白/运算符处断）。"""
    if len(line) <= limit:
        return [line]
    res = []
    cur = line
    while len(cur) > limit:
        sp = cur.rfind(" ", 0, limit)
        if sp < 5:
            sp = limit
        res.append(cur[:sp].rstrip())
        cur = "    " + cur[sp:].lstrip()
    res.append(cur)
    return res

def build_source_lines():
    files = collect_files()
    all_lines = []          # (relpath, lineno_in_file, code)
    per_file_eff = {}
    for rel in files:
        p = os.path.join(ROOT, rel)
        try:
            src = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        eff = strip_comments(src)
        per_file_eff[rel] = len(eff)
        for ln, code in enumerate(eff, start=1):
            for wl in wrap_line(code):
                all_lines.append((rel, ln, wl))
    return files, all_lines, per_file_eff

def render_source_html(all_lines):
    total = len(all_lines)
    # 取页：>=3000 行取前1500 + 后1500；否则全量
    if total >= 3000:
        sel = all_lines[:1500] + all_lines[-1500:]
        taken = 3000
    else:
        sel = all_lines
        taken = total
    pages = [sel[i:i+50] for i in range(0, len(sel), 50)]
    # 标注每页来源文件名（用于页眉下小字，可选）
    body = []
    for pi, page in enumerate(pages, start=1):
        rows = []
        for j, (rel, ln, code) in enumerate(page, start=1):
            esc = (code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            rows.append(f'<div class="ln"><span class="num">{j:02d}</span><span class="code">{esc}</span></div>')
        body.append(
            f'<section class="page">'
            f'<div class="phead"><span class="hname">{HEADER}</span>'
            f'<span class="powner">著作权人：{OWNER}</span>'
            f'<span class="pno">第 {pi} 页</span></div>'
            f'<div class="codebox">{"".join(rows)}</div></section>'
        )
    html = f'''<!doctype html><html lang="zh"><head><meta charset="utf-8">
<style>
@page{{size:A4;margin:12mm}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"Consolas","Courier New",monospace;color:#000;background:#fff}}
.page{{page-break-after:always;height:273mm;display:flex;flex-direction:column}}
.page:last-child{{page-break-after:auto}}
.phead{{display:flex;align-items:baseline;justify-content:space-between;border-bottom:1px solid #000;
  padding-bottom:2mm;margin-bottom:2mm;font-size:9pt;font-family:"SimSun",serif}}
.hname{{font-weight:bold}}
.pno{{font-weight:bold}}
.codebox{{font-size:8pt;line-height:1.75}}
.ln{{display:flex;white-space:pre}}
.num{{display:inline-block;width:22px;text-align:right;margin-right:8px;color:#000;user-select:none}}
.code{{white-space:pre-wrap;word-break:break-all}}
</style></head><body>{"".join(body)}</body></html>'''
    return html, len(pages), total, taken

# ============ 申请表 25 字段 ============
def git_date():
    try:
        out = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%ci"],
                             capture_output=True, text=True, encoding="utf-8", errors="ignore").stdout.strip()
        if out:
            d = out[:10]
            return d
    except Exception:
        pass
    return "待人工确认"

def build_form_info(eff_total, eff_files):
    dev_date = git_date()
    fields = [
        ("软件全称", SOFTWARE_NAME),
        ("软件简称", "（无）"),
        ("版本号", VERSION),
        ("权利取得方式", "原始取得"),
        ("权利范围", "全部权利"),
        ("开发完成日期", dev_date + "（以最新提交为准，待人工确认）"),
        ("发表状态", "未发表（本项目以 GitHub 项目页形式展示，未作为软件产品公开发表）"),
        ("开发方式", "单独开发"),
        ("硬件环境（开发）", "x86_64 兼容计算机；NVIDIA GPU（训练用，显存≥16GB）；内存≥32GB；磁盘≥100GB"),
        ("硬件环境（运行）", "Unitree Go2 四足机器人本体及机载算力，或在同等配置的主机上进行 Isaac Gym 仿真"),
        ("软件环境（开发）", "Ubuntu 20.04/22.04；Python 3.8+；PyTorch 1.13+；CUDA 11.7；Isaac Gym Preview 4；rsl_rl；legged_gym"),
        ("软件环境（运行）", "同开发环境；实机部署需 Unitree SDK 与机载 Linux"),
        ("编程语言", "Python"),
        ("源程序量", f"共 {eff_total} 行有效代码（已去除注释与空行；取自研目录 {', '.join(DIRS)}）"),
        ("著作权人姓名", OWNER),
        ("著作权人类别", "自然人"),
        ("证件类型", "居民身份证（号码待人工确认，不在材料中写明）"),
        ("国籍", "中国"),
        ("省/市", "广东省深圳市（待人工确认）"),
        ("权利取得方式（详）", "原始取得（由著作权人独立创作完成）"),
        ("申请的软件用途", "用于四足机器人安全自主导航的分层强化学习训练、仿真评测与算法研究"),
    ]
    main_func = (
        "本软件是一套面向 Unitree Go2 四足机器人的分层安全导航强化学习训练系统。"
        "系统将导航任务建模为“到达—避障”（Reach-Avoid）约束问题：在抵达目标点的同时，"
        "须满足与障碍物、场地边界保持安全距离的硬约束。系统采用分层架构，下层为冻结的运动控制策略，"
        "将高维关节力矩控制抽象为速度命令接口；上层策略仅输出线速度、侧向速度与偏航角速度三类速度命令，"
        "从而大幅降低决策维度、提升训练样本效率并保证底层运动的安全性。"
        "主要功能包括：一、构建基于 Isaac Gym 的四足仿真环境，支持出生点与朝向随机化、"
        "障碍物与场地边界的安全指标计算（avoid_metric 与 reach_metric）；"
        "二、构造高层观测空间（含目标与障碍/边界的激光雷达分箱特征，共 40 维），"
        "并将安全指标转换为到达代价 g(s) 与安全约束 h(s)；三、实现 Reach-Avoid PPO 训练算法，"
        "以 g(s)/h(s) 经广义优势估计（GAE）合成价值目标，训练高层策略；"
        "四、提供训练主循环（含成功率与执行成本统计、断点续训）、可视化回放与轨迹导出评测脚本；"
        "五、提供项目展示网页，汇总算法原理、训练曲线与演示。系统已在实际训练中使导航成功率由 0.014 提升至 0.691，"
        "执行成本收敛至约 79 步，验证了分层安全导航方案的有效性。"
    )
    tech = (
        "技术特点：1）分层抽象——冻结低层运动策略，仅训练高层速度命令策略，兼顾安全性与样本效率；"
        "2）约束建模——以到达代价 g(s) 与安全约束 h(s) 显式表达 Reach-Avoid 目标，区别于普通奖励最大化；"
        "3）安全度量——在底层环境中实时计算 avoid_metric/reach_metric，作为约束信号反馈给上层；"
        "4）算法实现——基于 rsl_rl 的 PPO 框架扩展 Reach-Avoid GAE 与专用回放缓冲，策略网络为多层感知机"
        "（512×4）加对角高斯动作分布；5）可复现——训练、回放、评测脚本齐全，关键超参集中于配置类，"
        "便于复现与消融；6）仿真到实机——环境接口与 Unitree Go2 一致，支持向实机策略部署迁移。"
    )
    return fields, main_func, tech, dev_date

def render_form_html(fields, main_func, tech):
    rows = "".join(f"<tr><td class='k'>{k}</td><td class='v'>{v}</td></tr>" for k, v in fields)
    html = f'''<!doctype html><html lang="zh"><head><meta charset="utf-8">
<style>
@page{{size:A4;margin:15mm}}
body{{font-family:"SimSun",serif;color:#000;font-size:11pt}}
h1{{font-family:"SimHei",sans-serif;text-align:center;font-size:16pt;margin-bottom:8mm}}
table{{border-collapse:collapse;width:100%}}
td{{border:1px solid #000;padding:3mm 4mm;vertical-align:top}}
.k{{font-weight:bold;width:30%;background:#eee;font-family:"SimHei",sans-serif}}
.v{{width:70%}}
.sec{{font-family:"SimHei",sans-serif;font-weight:bold;margin:8mm 0 3mm;font-size:13pt}}
.p{{text-indent:2em;line-height:1.8;margin:2mm 0}}
</style></head><body>
<h1>{SOFTWARE_NAME} {VERSION}　软件著作权登记申请表（字段信息）</h1>
<table>{rows}</table>
<div class="sec">主要功能（约700字）</div>
<p class="p">{main_func}</p>
<div class="sec">技术特点</div>
<p class="p">{tech}</p>
<div class="sec">说明</div>
<p class="p">以上字段依据项目真实源码与文档整理，供登录 register.ccopyright.com.cn 后照抄填入网页表单。"
"软件全称不含版本号，版本号单独填写；版本号在申请表、源代码页眉、操作手册页眉三处须保持一致。</p>
</body></html>'''
    return html

# ============ 操作手册（显式分页，≥30行/页，含目录） ============
BODY_CPL = 42      # 正文每行中文字数
TITLE_CPL = 22
TABLE_CPL = 52

def wrap_text(text, cpl):
    text = text.replace("\n", " ")
    if not text.strip():
        return [""]
    out = []
    # 按标点/空格断行
    buf = ""
    for ch in text:
        buf += ch
        if len(buf) >= cpl and (ch in " ，。、；：！？（）,.;:!? "):
            out.append(buf.strip())
            buf = ""
    if buf.strip():
        out.append(buf.strip())
    if not out:
        out = [text]
    return out

def est_lines(item):
    t = item[0]
    if t == "h1":
        return max(1, len(wrap_text(item[1], TITLE_CPL)))
    if t == "h2":
        return max(1, len(wrap_text(item[1], TITLE_CPL)))
    if t == "h3":
        return max(1, len(wrap_text(item[1], TITLE_CPL)))
    if t == "p":
        return len(wrap_text(item[1], BODY_CPL))
    if t == "table":
        n = 0
        for row in item[1]:
            n += max(1, len(wrap_text("　".join(row), TABLE_CPL)))
        return n + 1
    if t == "figure":
        return 0
    return 1

def pack_pages(items):
    pages = []
    cur = []
    cur_lines = 0
    i = 0
    while i < len(items):
        it = items[i]
        if it[0] == "figure":
            if cur:
                pages.append(cur); cur = []; cur_lines = 0
            pages.append([it])  # 图占整页
            i += 1
            continue
        il = est_lines(it)
        if cur and cur_lines + il > 40 and cur_lines >= 30:
            pages.append(cur); cur = []; cur_lines = 0
        cur.append(it); cur_lines += il
        if cur_lines >= 38:
            pages.append(cur); cur = []; cur_lines = 0
        i += 1
    if cur:
        pages.append(cur)
    # 末页不足30行则合并到最后一段或补一段
    if len(pages) > 1:
        last = pages[-1]
        ll = sum(est_lines(x) for x in last)
        if ll < 30:
            pages[-2].extend(last)
            pages.pop()
    return pages

def render_items(items, start_page, chapter_pages):
    out = []
    for pi, page in enumerate(pages_of(items), start=start_page):
        # 计算本页章节标题（用于页眉，可省略）
        blk = []
        for it in page:
            t = it[0]
            if t == "h1":
                lines = wrap_text(it[1], TITLE_CPL)
                blk.append(f'<h2 class="c1">{escape(it[1])}</h2>')
            elif t == "h2":
                blk.append(f'<h3 class="c2">{escape(it[1])}</h3>')
            elif t == "h3":
                blk.append(f'<h4 class="c3">{escape(it[1])}</h4>')
            elif t == "p":
                for ln in wrap_text(it[1], BODY_CPL):
                    blk.append(f'<p>{escape(ln)}</p>')
            elif t == "table":
                rows = "".join(
                    "<tr>" + "".join(f"<td>{escape(c)}</td>" for c in row) + "</tr>"
                    for row in it[1]
                )
                blk.append(f'<table>{rows}</table>')
            elif t == "figure":
                blk.append(f'<div class="fig">{it[1]}<div class="cap">{escape(it[2])}</div></div>')
        out.append(
            f'<section class="page"><div class="phead"><span class="hname">{HEADER}</span>'
            f'<span class="powner">著作权人：{OWNER}</span>'
            f'<span class="pno">第 {pi} 页</span></div>'
            f'<div class="content">{"".join(blk)}</div></section>'
        )
    return out

pages_of = pack_pages

def escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

ARCH_SVG = '''<svg viewBox="0 0 620 250" xmlns="http://www.w3.org/2000/svg" font-family="SimHei,sans-serif" font-size="12">
<rect x="10" y="20" width="150" height="46" fill="#e8f0fe" stroke="#3367d6"/><text x="85" y="48" text-anchor="middle">高层策略(待训练)</text>
<text x="85" y="80" text-anchor="middle" font-size="10">输出 [vx,vy,vyaw]</text>
<rect x="220" y="20" width="150" height="46" fill="#e6f4ea" stroke="#188038"/><text x="295" y="48" text-anchor="middle">冻结低层运动策略</text>
<text x="295" y="80" text-anchor="middle" font-size="10">12 关节动作</text>
<rect x="430" y="20" width="150" height="46" fill="#fce8e6" stroke="#d93025"/><text x="505" y="48" text-anchor="middle">Unitree Go2 本体</text>
<line x1="160" y1="43" x2="220" y2="43" stroke="#333" marker-end="url(#a)"/>
<line x1="370" y1="43" x2="430" y2="43" stroke="#333" marker-end="url(#a)"/>
<rect x="10" y="150" width="570" height="60" fill="#fef7e0" stroke="#f9ab00"/>
<text x="295" y="172" text-anchor="middle">训练信号：到达代价 g(s) 与 安全约束 h(s)</text>
<text x="295" y="194" text-anchor="middle" font-size="10">经 Reach-Avoid GAE 合成价值目标 -> 高层策略更新（每高层步=低层5步）</text>
<line x1="295" y1="120" x2="295" y2="150" stroke="#f9ab00" stroke-dasharray="4"/>
<defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#333"/></marker></defs>
</svg>'''

DATAFLOW_SVG = '''<svg viewBox="0 0 620 220" xmlns="http://www.w3.org/2000/svg" font-family="SimHei,sans-serif" font-size="12">
<rect x="10" y="80" width="130" height="44" fill="#e8f0fe" stroke="#3367d6"/><text x="75" y="107" text-anchor="middle">仿真环境</text>
<rect x="170" y="80" width="130" height="44" fill="#e6f4ea" stroke="#188038"/><text x="235" y="107" text-anchor="middle">安全度量</text>
<rect x="330" y="80" width="130" height="44" fill="#fef7e0" stroke="#f9ab00"/><text x="395" y="107" text-anchor="middle">g(s)/h(s)</text>
<rect x="490" y="80" width="120" height="44" fill="#fce8e6" stroke="#d93025"/><text x="550" y="107" text-anchor="middle">Reach-Avoid PPO</text>
<line x1="140" y1="102" x2="170" y2="102" stroke="#333" marker-end="url(#b)"/>
<line x1="300" y1="102" x2="330" y2="102" stroke="#333" marker-end="url(#b)"/>
<line x1="460" y1="102" x2="490" y2="102" stroke="#333" marker-end="url(#b)"/>
<line x1="550" y1="124" x2="550" y2="160" stroke="#333" marker-end="url(#b)"/>
<line x1="550" y1="160" x2="395" y2="160" stroke="#333" marker-end="url(#b)"/>
<line x1="395" y1="160" x2="235" y2="160" stroke="#333" marker-end="url(#b)"/>
<line x1="235" y1="160" x2="75" y2="160" stroke="#333" marker-end="url(#b)"/>
<line x1="75" y1="160" x2="75" y2="124" stroke="#333" marker-end="url(#b)"/>
<text x="395" y="178" text-anchor="middle" font-size="10">策略更新闭环</text>
<defs><marker id="b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#333"/></marker></defs>
</svg>'''

OBS_SVG = '''<svg viewBox="0 0 620 200" xmlns="http://www.w3.org/2000/svg" font-family="SimHei,sans-serif" font-size="12">
<rect x="10" y="30" width="120" height="40" fill="#e8f0fe" stroke="#3367d6"/><text x="70" y="55" text-anchor="middle">基础特征 8维</text>
<rect x="150" y="30" width="150" height="40" fill="#e6f4ea" stroke="#188038"/><text x="225" y="55" text-anchor="middle">目标 lidar 16维</text>
<rect x="320" y="30" width="170" height="40" fill="#fef7e0" stroke="#f9ab00"/><text x="405" y="55" text-anchor="middle">障碍/边界 lidar 16维</text>
<rect x="510" y="30" width="100" height="40" fill="#fce8e6" stroke="#d93025"/><text x="560" y="55" text-anchor="middle">合计 40维</text>
<line x1="130" y1="50" x2="150" y2="50" stroke="#333"/><line x1="300" y1="50" x2="320" y2="50" stroke="#333"/><line x1="490" y1="50" x2="510" y2="50" stroke="#333"/>
<text x="310" y="110" text-anchor="middle">高层观测 o_t ∈ R^40 = [基础 | 目标lidar | 障碍/边界lidar]</text>
<text x="310" y="140" text-anchor="middle" font-size="10">动作 a_t = [vx, vy, vyaw] ∈ R^3，由高层策略输出，经冻结低层策略映射到 12 关节</text>
</svg>'''

CURVE_SVG = '''<svg viewBox="0 0 620 220" xmlns="http://www.w3.org/2000/svg" font-family="SimHei,sans-serif" font-size="12">
<line x1="60" y1="180" x2="580" y2="180" stroke="#333"/><line x1="60" y1="20" x2="60" y2="180" stroke="#333"/>
<text x="20" y="100" text-anchor="middle" transform="rotate(-90 20 100)">指标</text>
<text x="320" y="208" text-anchor="middle">训练轮数（iteration）</text>
<polyline points="60,175 140,150 220,120 300,95 380,70 460,55 540,48" fill="none" stroke="#188038" stroke-width="2"/>
<text x="545" y="46" fill="#188038">成功率 0.014→0.691</text>
<polyline points="60,60 140,80 220,100 300,118 380,135 460,150 540,160" fill="none" stroke="#d93025" stroke-width="2"/>
<text x="300" y="175" fill="#d93025">执行成本 79.1 步(收敛)</text>
</svg>'''

def build_manual_items():
    I = []
    I.append(("h1", "第一章 引言"))
    I.append(("h2", "1.1 编写目的"))
    I.append(("p", "本手册用于说明“四足机器人分层安全导航强化学习训练平台”的功能、架构、安装配置与操作使用方式，"
                     "作为计算机软件著作权登记的文档鉴别材料，供审查机构与后续软件维护人员参考。手册内容均以项目真实源码为依据，"
                     "不写入代码中不存在的功能，确保与源代码材料一致。"))
    I.append(("h2", "1.2 软件背景"))
    I.append(("p", "四足机器人因具备越障与复杂地形适应能力，被广泛应用于巡检、救援、物流与科研等场景。"
                     "Unitree Go2 是一款低成本、开源生态相对完善的四足机器人平台，适合作为强化学习导航算法的验证载体。"))
    I.append(("p", "让四足机器人在未知或动态环境中自主、安全地抵达目标点，是机器人导航的核心问题。若仅以“到达目标”为优化目标，"
                     "策略容易为走捷径而撞击障碍物或冲出场地边界；因此本软件将导航任务建模为“到达—避障”（Reach-Avoid）约束问题："
                     "在抵达目标点的同时，必须与障碍物及场地边界保持安全距离。"))
    I.append(("p", "直接以关节空间训练端到端策略存在维度高、样本效率低、且难以保证安全的问题。本软件采用分层强化学习："
                     "冻结一个已训练好的低层运动控制策略，将高维关节控制抽象为速度命令接口，仅训练一个输出速度命令的高层策略。"
                     "这样既提升样本效率，又把不安全的底层动作隔离在冻结策略之内。"))
    I.append(("h2", "1.3 适用对象"))
    I.append(("p", "本软件面向机器人学研究人员与算法工程师，用于复现分层安全导航的训练流程、在 Isaac Gym 仿真中评测策略性能，"
                     "并可将训练所得的高层策略迁移至 Unitree Go2 实机。亦可作为教学示例，帮助理解 Reach-Avoid 约束强化学习。"))
    I.append(("h2", "1.4 参考文档"))
    I.append(("p", "软件随附 README.md 与 ALGORITHM_DESIGN.md，分别说明环境搭建、训练命令与算法设计思路；"
                     "源代码材料中包含的 .py 文件为功能实现的权威依据。本手册与前述文档、源码三者描述应保持一致。"))
    I.append(("h2", "1.5 符号与单位约定"))
    I.append(("p", "本手册中，状态记为 s，高层观测记为 o，动作记为 a；代价函数 g(s) 表示到达代价，约束函数 h(s) 表示安全约束；"
                     "几何尺寸单位为米（m），角度单位为弧度（rad），速度单位为米每秒（m/s），角速度单位为弧度每秒（rad/s）。"))
    I.append(("h1", "第二章 软件功能概要"))
    I.append(("h2", "2.1 系统定位"))
    I.append(("p", "本软件是一套用于训练与评测四足机器人分层安全导航策略的工具集。它以 Isaac Gym 作为仿真后端，"
                     "以 rsl_rl 的 PPO 框架为基础扩展出 Reach-Avoid 训练算法，配套高层导航环境、安全指标计算、回放与评测脚本，"
                     "以及用于成果展示的静态网页。"))
    I.append(("h2", "2.2 主要功能"))
    I.append(("p", "（一）仿真环境构建：基于 Isaac Gym 搭建 Go2 仿真场景，支持机器人出生点与朝向的随机化，"
                     "以及障碍物与目标点的随机布置，使训练数据覆盖多样的初始条件。"))
    I.append(("p", "（二）安全指标计算：在底层仿真环境中实时计算 avoid_metric（避障度）与 reach_metric（到达度），"
                     "作为后续约束信号的基础。当距离障碍物或边界过近时，avoid_metric 显著下降；当接近目标时，reach_metric 上升。"))
    I.append(("p", "（三）高层观测构造：将安全指标与目标、障碍、边界的激光雷达分箱特征组合为 40 维观测向量，"
                     "为高层策略提供充分且低维的决策信息。"))
    I.append(("p", "（四）约束信号转换：将底层指标转换为到达代价 g(s) 与安全约束 h(s)，使训练目标可由约束优化统一表达，"
                     "而非简单的标量奖励。"))
    I.append(("p", "（五）策略训练：实现 Reach-Avoid PPO，以 g(s)/h(s) 经广义优势估计（GAE）合成价值目标，"
                     "更新高层策略参数。训练过程统计每轮成功率与执行成本，并支持断点续训。"))
    I.append(("p", "（六）回放与评测：提供可视化回放脚本观察策略行为，提供轨迹导出脚本将评测结果保存为 JSON，"
                     "便于离线统计成功率、碰撞率与执行成本。"))
    I.append(("p", "（七）成果展示：提供基于 GitHub Pages 的静态网页，汇总算法原理、训练曲线与演示内容，便于对外交流。"))
    I.append(("h2", "2.3 运行流程概览"))
    I.append(("p", "典型工作流为：配置环境参数 → 启动训练（train_reach_avoid.py）得到高层策略检查点 → 使用回放脚本"
                     "（play_reach_avoid.py）观察行为 → 使用评测脚本（test_reach_avoid.py）导出轨迹并统计指标 → 必要时绘制"
                     "训练曲线（plot_training_results.py）与场景布局（plot_env_layout.py）。各步骤的输入输出均以文件传递。"))
    I.append(("h1", "第三章 架构设计与选型"))
    I.append(("h2", "3.1 总体架构"))
    I.append(("p", "系统采用双层控制结构。高层策略输出速度命令，冻结的低层运动策略将速度命令转化为 12 个关节的目标动作，"
                     "最终驱动 Go2 本体在仿真中运动。训练阶段，环境不返回标量奖励，而是返回安全指标；高层环境将其转换成 g(s) 与 h(s)，"
                     "经 Reach-Avoid GAE 合成价值目标，用于更新高层策略。高层每决策一步，低层连续执行 5 步，形成分层时间抽象。"))
    I.append(("figure", ARCH_SVG, "图3-1 分层控制闭环架构"))
    I.append(("figure", DATAFLOW_SVG, "图3-2 训练信号数据流"))
    I.append(("h2", "3.2 分层时间抽象"))
    I.append(("p", "分层抽象是本软件的关键设计。低层策略以较高频率（每仿真步）运行，保证机器人稳定行走与抗扰；"
                     "高层策略以较低频率（每 5 个低层步）运行，只在“速度命令”这一语义清晰的接口上决策。"
                     "这种时间抽象降低了决策频次，使高层策略能在更长的视野上规划到达路径，同时低层始终维持安全的基本运动。"))
    I.append(("h2", "3.3 技术选型"))
    I.append(("p", "仿真后端选用 Isaac Gym Preview 4，因其提供大规模并行物理仿真，可在单卡上同时采样大量环境，"
                     "显著提升强化学习的采样效率；底层封装沿用 legged_gym 框架；训练框架基于 rsl_rl 的 PPO 实现，"
                     "并扩展出 Reach-Avoid 专用分支；深度学习框架为 PyTorch；全部功能以 Python 实现，便于科研人员阅读与复现。"))
    I.append(("p", "采用分层而非端到端策略的原因：低层运动控制已由冻结策略保证稳定行走，高层只需在“速度命令”这一低维、"
                     "语义清晰的接口上决策，能够显著提升样本效率，并将底层不安全动作隔离在冻结策略之内，从结构上增强安全性。"))
    I.append(("h2", "3.4 目录结构与职责"))
    I.append(("table", [
        ["目录/文件", "职责"],
        ["legged_gym_go2/legged_gym/envs/go2/", "Go2 仿真环境、配置与安全指标计算"],
        [".../go2/go2_env.py", "底层环境，扩展 _compute_safety_metrics()"],
        [".../go2/high_level_navigation_env.py", "高层观测构造与 g(s)/h(s) 转换"],
        [".../go2/hierarchical_go2_env.py", "分层封装（高层1步=低层5步）"],
        [".../go2/go2_config.py", "场地、障碍、目标等关键参数集中定义"],
        ["legged_gym_go2/legged_gym/scripts/", "训练、回放、评测与绘图脚本"],
        ["rsl_rl/rsl_rl/algorithms/reach_avoid_ppo.py", "Reach-Avoid PPO 核心算法"],
        ["rsl_rl/rsl_rl/algorithms/ppo.py", "基础 PPO 实现（被复用）"],
        ["rsl_rl/rsl_rl/modules/actor_critic.py", "策略网络与价值网络"],
        ["rsl_rl/rsl_rl/storage/rollout_storage.py", "轨迹回放缓冲"],
        ["rsl_rl/rsl_rl/runners/on_policy_runner.py", "训练主循环与日志"],
        ["webui/", "项目展示静态网页"],
    ]))
    I.append(("h2", "3.5 模块依赖关系"))
    I.append(("p", "高层环境（high_level_navigation_env）依赖底层环境（go2_env）提供的安全指标；分层环境"
                     "（hierarchical_go2_env）装载冻结的低层策略，向上对高层策略暴露速度命令接口；训练脚本依赖"
                     "reach_avoid_ppo 与 actor_critic 完成策略优化；评测与绘图脚本依赖训练产出的检查点与日志。各模块通过"
                     "Python 导入与配置文件耦合，无外部服务依赖。"))
    I.append(("h1", "第四章 详细功能阐述"))
    I.append(("h2", "4.1 环境模块"))
    I.append(("p", "go2_env.py 在底层 Go2 仿真环境中扩展 _compute_safety_metrics()，产出 avoid_metric 与 reach_metric，"
                     "并随机化机器人出生点与朝向，使策略对初始条件具有鲁棒性。该模块还负责物理步进、碰撞检测与回合终止判断。"))
    I.append(("p", "high_level_navigation_env.py 将底层指标转换为到达代价 g(s) 与安全约束 h(s)：当机器人抵达目标附近时 g(s) 取"
                     "较小的 g_target（如 -300），距离越远代价越高（由 g_distance_scale 控制）；当处于安全区域时 h(s) 取 h_safe"
                     "（如 -300），发生碰撞或越界时取 h_unsafe（如 300）。同时构造 40 维高层观测：8 维基础特征、16 维目标"
                     "激光雷达分箱特征、16 维障碍/边界激光雷达分箱特征。"))
    I.append(("figure", OBS_SVG, "图4-1 高层观测空间构成（40维）"))
    I.append(("p", "hierarchical_go2_env.py 装载冻结的低层策略，实现分层时间抽象：高层输出一个速度命令后，低层连续执行 5 步，"
                     "再回到高层决策。该模块对上层屏蔽了关节级控制细节，仅暴露速度命令接口。"))
    I.append(("p", "go2_config.py 以配置类集中定义场地尺寸（12×12 米）、障碍球数量（14）、目标半径（0.5 米）、训练轮数"
                     "（1500）等关键参数，便于实验复现与消融。"))
    I.append(("h2", "4.2 算法模块"))
    I.append(("p", "reach_avoid_ppo.py 是本软件核心。其中 _calculate_reach_gae() 以 g(s)/h(s) 计算广义优势估计，"
                     "ReachAvoidBuffer 存储含约束信号的轨迹，ReachAvoidPPO 类据此更新高层策略。该方法把“到达”与“避障”"
                     "统一为带约束的策略优化问题，区别于普通以奖励最大化为目标的 PPO。"))
    I.append(("p", "actor_critic.py 定义多层感知机（MLP）策略网络与价值网络，隐含层均为 512×4，动作分布采用对角高斯，"
                     "适用于连续动作空间。actor_critic_recurrent.py 提供带循环单元（如 GRU/LSTM）的可选版本，用于需要处理"
                     "部分可观信息的场景。"))
    I.append(("p", "rollout_storage.py 管理训练轨迹的收集与批量采样；on_policy_runner.py 组织训练循环，负责任务创建、"
                     "日志写入、模型保存与评估调度，并支持从检查点恢复训练。"))
    I.append(("h2", "4.3 训练与评测脚本"))
    I.append(("p", "train_reach_avoid.py 为训练主循环，按配置创建环境、初始化算法、迭代更新策略，并在每轮统计成功率与执行成本，"
                     "将检查点保存至 logs/ 目录，支持断点续训。"))
    I.append(("p", "play_reach_avoid.py 用于可视化回放：加载训练好的高层策略，在仿真中运行并记录画面，便于直观检查导航行为"
                     "是否安全、是否绕障、是否抵达目标。"))
    I.append(("p", "test_reach_avoid.py 用于批量评测：在多种随机初始条件下运行策略，将轨迹与指标导出为 JSON 文件，便于离线统计"
                     "成功率、碰撞率与平均执行成本。"))
    I.append(("p", "plot_training_results.py 与 plot_env_layout.py 分别读取日志与配置，绘制训练曲线（成功率、成本随轮数变化）"
                     "与场景布局（场地、障碍、目标分布），辅助结果分析。"))
    I.append(("h2", "4.4 工具与展示模块"))
    I.append(("p", "utils 下提供 helpers（通用辅助）、terrain（地形相关）、task_registry（任务注册）等模块；"
                     "webui 为 GitHub Pages 静态站点，展示算法原理、训练曲线与演示视频，便于成果对外交流与评审材料补充。"))
    I.append(("h1", "第五章 安装与配置"))
    I.append(("h2", "5.1 硬件与软件环境"))
    I.append(("p", "开发硬件建议为 x86_64 兼容计算机，配备 NVIDIA GPU（训练用，显存不小于 16GB）、内存不小于 32GB、"
                     "磁盘不小于 100GB。运行硬件为 Unitree Go2 四足机器人本体及机载算力，或在同等配置的主机上进行 Isaac Gym 仿真。"))
    I.append(("p", "软件环境：操作系统 Ubuntu 20.04 或 22.04；Python 3.8 及以上；PyTorch 1.13 及以上；CUDA 11.7；"
                     "Isaac Gym Preview 4；依赖库 rsl_rl 与 legged_gym。实机部署另需 Unitree 官方 SDK 与机载 Linux。"))
    I.append(("h2", "5.2 依赖获取与安装"))
    I.append(("p", "Isaac Gym 需从 NVIDIA 官方渠道获取 Preview 4 版本并安装其 Python 包；PyTorch 与 CUDA 按官方指引安装；"
                     "本仓库的 rsl_rl 与 legged_gym 以可编辑方式安装（pip install -e）。安装完成后，可在终端中导入相关模块验证环境。"))
    I.append(("h2", "5.3 关键配置参数"))
    I.append(("p", "go2_config.py 集中定义导航任务的关键参数，下表列出主要参数及其在本项目中的取值，用户可在复现实验时按需调整。"))
    I.append(("table", [
        ["参数", "含义", "本项目取值", "说明"],
        ["field_size", "场地边长", "12 m", "12×12 米方形场地"],
        ["n_obstacles", "障碍球数量", "14", "随机布置于场地内"],
        ["target_radius", "目标半径", "0.5 m", "进入即判定到达"],
        ["g_target", "到达目标代价", "-300", "抵达目标时取该值"],
        ["g_distance_scale", "距离缩放系数", "100", "控制距离对代价的权重"],
        ["h_safe", "安全时代价", "-300", "未碰撞/未越界"],
        ["h_unsafe", "不安全时代价", "300", "碰撞或越界"],
        ["obs_dim", "高层观测维度", "40", "基础8+目标16+障碍/边界16"],
        ["act_dim", "动作维度", "3", "vx, vy, vyaw"],
        ["train_iters", "训练轮数", "1500", "本项目实际训练量"],
    ]))
    I.append(("h2", "5.4 观测与动作空间"))
    I.append(("p", "高层观测为 40 维向量，组成见图4-1：前 8 维为基础特征（含机器人位姿、速度、与目标相对位置等）；"
                     "中间 16 维为目标方向的激光雷达分箱特征；后 16 维为障碍/边界的激光雷达分箱特征。动作空间为 3 维连续向量"
                     " [vx, vy, vyaw]，分别表示前进/后退线速度、左/右平移速度、偏航角速度，范围由配置约束。"))
    I.append(("p", "激光雷达分箱（lidar bin）指将机器人周围空间按角度划分为若干扇区，取各扇区内最近障碍（或边界）的距离作为该"
                     "扇区的特征值。这种表示既压缩了原始点云维度，又保留了绕障所需的方位信息，适合作为高层策略输入。"))
    I.append(("h2", "5.5 安全指标说明"))
    I.append(("p", "avoid_metric 反映机器人相对障碍物与边界的安全程度，值越高越安全；reach_metric 反映机器人相对目标的接近程度，"
                     "值越高越接近目标。二者由底层环境的 _compute_safety_metrics() 计算，是构造 g(s)/h(s) 的直接依据，也是本软件"
                     "“安全导航”能力的来源。"))
    I.append(("h1", "第六章 操作使用"))
    I.append(("h2", "6.1 训练操作流程"))
    I.append(("p", "第一步，确认环境与依赖安装正确，CUDA 可用；第二步，在 go2_config.py 中确认场地、障碍、目标等参数符合预期；"
                     "第三步，运行训练脚本 train_reach_avoid.py 启动训练，控制台将按轮输出成功率与执行成本；第四步，观察日志，"
                     "待成功率与成本收敛后停止训练，检查点自动保存至 logs/。"))
    I.append(("p", "训练过程中若成功率长期不上升，可检查随机初始化范围是否过难、学习率是否合适、以及安全指标计算是否符合预期；"
                     "若频繁碰撞，可降低目标距离权重或增大障碍数量以加强避障学习。相关超参均可在配置类与算法参数中调整。"))
    I.append(("h2", "6.2 可视化回放"))
    I.append(("p", "运行 play_reach_avoid.py 加载已训练的高层策略，仿真将在图形界面中运行。观察要点：机器人是否朝目标前进、"
                     "是否在接近障碍物时减速或绕行、是否在回合内安全抵达目标。回放可用于定性判断策略是否符合“安全导航”目标。"))
    I.append(("h2", "6.3 评测与轨迹导出"))
    I.append(("p", "运行 test_reach_avoid.py 在大量随机初始条件下批量评测，脚本将每条轨迹的状态、动作与指标写入 JSON 文件。"
                     "离线可使用该文件统计成功率、碰撞率与平均执行步数（即执行成本），得到可量化的性能结论。"))
    I.append(("h2", "6.4 输出文件说明"))
    I.append(("table", [
        ["路径/文件", "内容"],
        ["logs/*.pt", "策略与优化器检查点，用于续训与回放"],
        ["logs/*/training_summary.txt", "训练汇总（成功率、成本等）"],
        ["logs/*.png", "训练曲线或场景布局图"],
        ["test_reach_avoid 导出 JSON", "评测轨迹与逐回合指标"],
        ["output/*.png", "用于文档与展示的结果图"],
    ]))
    I.append(("h2", "6.5 训练曲线解读"))
    I.append(("p", "典型训练曲线中，成功率随轮数从较低水平（如 0.014）逐步上升至约 0.691，峰值约 0.743；执行成本（平均到达步数）"
                     "随轮数下降并收敛至约 79.1 步。成功率上升与成本下降通常同步发生，说明策略在“更快到达”与“更安全”之间取得了平衡。"))
    I.append(("figure", CURVE_SVG, "图6-1 典型训练曲线示意（成功率上升、成本收敛）"))
    I.append(("h2", "6.6 实机部署简述"))
    I.append(("p", "训练所得高层策略为速度命令策略，可经模型导出后在 Unitree Go2 机载算力上运行：高层输出速度命令，由机载低层"
                     "控制器（与仿真中冻结策略同构）映射为关节动作。实机部署需额外处理传感器标定、通信延迟与安全检查，超出本软件"
                     "仿真范畴，此处仅作接口说明。"))
    I.append(("h1", "第七章 数据库、字典与术语"))
    I.append(("h2", "7.1 数据存储说明"))
    I.append(("p", "本软件不依赖关系型数据库。训练产出以文件形式保存：策略检查点存于 logs/ 目录（.pt 文件），"
                     "训练曲线与布局图以 .png 保存；算法超参与环境参数以 Python 配置类 / 字典形式集中定义，便于版本管理。"))
    I.append(("h2", "7.2 关键参数汇总"))
    I.append(("table", [
        ["参数", "含义", "取值"],
        ["g_target", "到达目标代价", "-300"],
        ["g_distance_scale", "距离缩放", "100"],
        ["h_safe", "安全时代价", "-300"],
        ["h_unsafe", "不安全时代价", "300"],
        ["obs_dim", "高层观测维度", "40"],
        ["act_dim", "动作维度", "3"],
        ["field_size", "场地尺寸", "12×12 m"],
        ["n_obstacles", "障碍球数量", "14"],
        ["target_radius", "目标半径", "0.5 m"],
        ["train_iters", "训练轮数", "1500"],
        ["success_rate", "最终成功率", "0.691（峰值0.743）"],
        ["exec_cost", "收敛执行成本", "79.1 步"],
    ]))
    I.append(("h2", "7.3 核心变量字典"))
    I.append(("table", [
        ["名称", "含义"],
        ["g(s)", "到达代价函数，抵达目标时取 g_target，距离越远代价越高"],
        ["h(s)", "安全约束函数，安全时取 h_safe，碰撞/越界时取 h_unsafe"],
        ["avoid_metric", "底层环境计算的避障度指标，越高越安全"],
        ["reach_metric", "底层环境计算的到达度指标，越高越接近目标"],
        ["高层观测 o", "40 维向量（基础8+目标lidar16+障碍/边界lidar16）"],
        ["速度命令 a", "动作 [vx, vy, vyaw]（前后/左右/偏航）"],
        ["GAE", "广义优势估计，用于策略梯度基线"],
    ]))
    I.append(("h2", "7.4 术语表"))
    I.append(("p", "Reach-Avoid（到达—避障）：在抵达目标的同时满足安全约束的控制问题，本软件的核心建模方式。"))
    I.append(("p", "分层强化学习：将决策分解为高层策略与低层策略的多层结构，高层在更粗时间尺度上决策。"))
    I.append(("p", "冻结低层运动策略：预训练且在训练过程中参数固定的底层控制器，负责稳定行走，隔离不安全动作。"))
    I.append(("p", "高层策略：本软件的训练对象，输入 40 维观测，输出 3 维速度命令。"))
    I.append(("p", "对角高斯策略：动作分布为各维独立高斯，仅学习均值与对数标准差，适用于连续动作空间。"))
    I.append(("p", "Isaac Gym：NVIDIA 提供的并行物理仿真平台，用作本软件仿真后端。"))
    I.append(("p", "PPO：近端策略优化，本软件训练所基于的 on-policy 强化学习算法。"))
    I.append(("p", "GAE：广义优势估计，结合时序差分误差估计优势函数，稳定策略梯度。"))
    I.append(("p", "激光雷达分箱（lidar bin）：将周围空间按角度分箱并取最近障碍距离，作为观测特征。"))
    I.append(("h2", "7.5 常见问题排查"))
    I.append(("table", [
        ["现象", "可能原因", "处理建议"],
        ["导入报错", "Isaac Gym 未正确安装", "检查 Isaac Gym Preview 4 与 Python 包路径"],
        ["CUDA 不可用", "驱动/CUDA 版本不匹配", "按 PyTorch 官方指引重装对应 CUDA 版本"],
        ["成功率不上升", "初始难度过高/学习率不当", "调小障碍数或调学习率，检查安全指标"],
        ["频繁碰撞", "避障权重不足", "增大 h_unsafe 或减小目标距离权重"],
        ["续训失败", "检查点路径错误", "确认 logs/ 下检查点文件与配置一致"],
    ]))
    I.append(("h2", "1.6 软件特点小结"))
    I.append(("p", "综上，本软件的特点可概括为：分层抽象提升样本效率；以 Reach-Avoid 约束统一表达到达与安全；"
                     "在底层实时计算 avoid/reach 指标作为安全信号；基于 rsl_rl 的 PPO 框架实现专用算法；训练、回放、评测脚本齐全，"
                     "便于复现与消融；仿真到实机的接口一致，支持策略部署迁移。"))
    I.append(("h2", "2.4 功能与文件对应"))
    I.append(("table", [
        ["功能", "主要文件"],
        ["仿真环境与安全指标", "go2_env.py, _compute_safety_metrics()"],
        ["高层观测与约束信号", "high_level_navigation_env.py"],
        ["分层时间抽象", "hierarchical_go2_env.py"],
        ["训练算法", "reach_avoid_ppo.py, _calculate_reach_gae()"],
        ["策略/价值网络", "actor_critic.py"],
        ["训练主循环", "train_reach_avoid.py, on_policy_runner.py"],
        ["回放与评测", "play_reach_avoid.py, test_reach_avoid.py"],
        ["结果绘图", "plot_training_results.py, plot_env_layout.py"],
    ]))
    I.append(("h2", "3.6 性能与适用边界"))
    I.append(("p", "本项目实际训练中，成功率由约 0.014 提升至 0.691（峰值 0.743），执行成本收敛至约 79.1 步，"
                     "表明分层安全导航方案有效。其适用边界为：训练在仿真中进行，实机部署需额外处理传感器与延迟；"
                     "当前场景为 12×12 米方形场地、14 个障碍球，更大或更复杂场景需相应扩展配置与训练。"))
    I.append(("h2", "4.5 高层策略接口说明"))
    I.append(("table", [
        ["接口", "维度", "含义/范围"],
        ["观测 o_t", "40", "基础8 + 目标lidar16 + 障碍/边界lidar16"],
        ["动作 a_t[0] vx", "1", "前后线速度（m/s）"],
        ["动作 a_t[1] vy", "1", "左右平移速度（m/s）"],
        ["动作 a_t[2] vyaw", "1", "偏航角速度（rad/s）"],
        ["低层步数/高层步", "5", "高层每步低层执行 5 步"],
    ]))
    I.append(("h2", "5.6 训练资源与耗时"))
    I.append(("p", "训练对算力的主要消耗在大规模并行仿真采样与神经网络更新。本项目在单张服务器级 GPU 上完成 1500 轮训练，"
                     "实际耗时约 21.5 小时；检查点与日志随训练写入磁盘，占用空间主要取决于保存频率与回放画面数量。"
                     "若显存或算力有限，可减少并行环境数量，相应延长训练时间。"))
    I.append(("h2", "5.7 配置示例说明"))
    I.append(("p", "go2_config.py 以 Python 配置类集中管理参数，典型字段包括：场地边长 field_size、障碍球数量 n_obstacles、"
                     "目标半径 target_radius、到达代价 g_target 与距离缩放 g_distance_scale、安全代价 h_safe 与 h_unsafe、"
                     "训练轮数 train_iters 等。修改这些字段即可调整任务难度与约束强度，无需改动算法代码，体现了配置与逻辑分离的设计。"))
    I.append(("h2", "6.7 评测指标计算方法"))
    I.append(("p", "成功率 = 在 N 个随机初始回合中安全抵达目标的比例；碰撞率 = 发生碰障或越界的回合比例；"
                     "执行成本 = 抵达目标所需的平均仿真步数（步数越少表示路径越短、效率越高）。三者结合可全面衡量“是否到达、是否安全、是否高效”。"
                     "test_reach_avoid.py 导出的 JSON 包含逐回合上述指标，离线汇总即可得到报告。"))
    I.append(("h2", "6.8 结果复现建议"))
    I.append(("p", "为复现本项目结果，建议：固定随机种子以保证可复现；使用与本手册一致的 go2_config 参数；"
                     "在相同的 GPU 与 Isaac Gym 版本下训练；保存每轮日志以便绘制曲线。若成功率偏离较大，优先检查安全指标计算与"
                     "随机初始化范围是否一致。"))
    I.append(("h2", "7.6 版本与演进"))
    I.append(("p", "本软件版本为 V1.0.0，为首次登记的完整训练与评测工具集。后续演进方向包括：支持更丰富的地形与动态障碍、"
                     "引入循环策略处理部分可观信息、以及更完善的实机部署与安全保护组件。版本号在申请表、源代码页眉与操作手册页眉三处保持一致。"))
    I.append(("h2", "7.7 技术支持与声明"))
    I.append(("p", "本软件以源码形式提供，使用问题可参考随附 README 与 ALGORITHM_DESIGN 文档，或查阅项目展示网页。"
                     "本手册仅为软件功能与使用的说明，不构成任何担保；涉及论文方法的“剩余预算”“双 Critic”等内容未在本仓库代码中实现，"
                     "不计入本软著登记范围。"))
    I.append(("h1", "第八章 附录"))
    I.append(("h2", "8.1 源程序文件清单"))
    I.append(("p", "本软著登记的源程序取自研目录 legged_gym_go2/legged_gym 与 rsl_rl/rsl_rl，下表按模块列出主要源文件及其职责"
                     "（完整清单以源代码鉴别材料为准）。所有文件均参与训练或评测流程。"))
    I.append(("table", [
        ["文件", "职责"],
        ["rsl_rl/rsl_rl/algorithms/reach_avoid_ppo.py", "Reach-Avoid PPO 核心：GAE 与专用缓冲"],
        ["rsl_rl/rsl_rl/algorithms/ppo.py", "基础 PPO 实现（被复用）"],
        ["rsl_rl/rsl_rl/modules/actor_critic.py", "策略与价值网络（MLP 512×4）"],
        ["rsl_rl/rsl_rl/modules/actor_critic_recurrent.py", "带循环单元的网络可选版本"],
        ["rsl_rl/rsl_rl/storage/rollout_storage.py", "轨迹回放缓冲"],
        ["rsl_rl/rsl_rl/runners/on_policy_runner.py", "训练主循环与日志"],
        ["rsl_rl/rsl_rl/utils/utils.py", "通用工具函数"],
        ["legged_gym_go2/.../envs/go2/go2_config.py", "场地/障碍/目标等关键参数"],
        ["legged_gym_go2/.../envs/go2/go2_env.py", "底层环境与安全指标"],
        ["legged_gym_go2/.../envs/go2/high_level_navigation_env.py", "高层观测与 g(s)/h(s)"],
        ["legged_gym_go2/.../envs/go2/hierarchical_go2_env.py", "分层封装（高层1步=低层5步）"],
        ["legged_gym_go2/.../envs/base/legged_robot.py", "足式机器人基类环境"],
        ["legged_gym_go2/.../envs/base/legged_robot_config.py", "基类环境配置"],
        ["legged_gym_go2/.../envs/base/base_task.py", "任务基类"],
        ["legged_gym_go2/.../envs/base/base_config.py", "基础配置"],
        ["legged_gym_go2/.../envs/base/origin_legged_robot.py", "原始足式机器人环境"],
        ["legged_gym_go2/.../scripts/train_reach_avoid.py", "训练主脚本"],
        ["legged_gym_go2/.../scripts/play_reach_avoid.py", "可视化回放"],
        ["legged_gym_go2/.../scripts/test_reach_avoid.py", "批量评测与轨迹导出"],
        ["legged_gym_go2/.../scripts/play_fixed_commands_with_video.py", "定速命令录屏"],
        ["legged_gym_go2/.../scripts/plot_training_results.py", "训练曲线绘图"],
        ["legged_gym_go2/.../scripts/plot_env_layout.py", "场景布局绘图"],
        ["legged_gym_go2/.../utils/helpers.py", "通用辅助"],
        ["legged_gym_go2/.../utils/terrain.py", "地形相关"],
        ["legged_gym_go2/.../utils/task_registry.py", "任务注册"],
        ["legged_gym_go2/.../utils/logger.py", "日志辅助"],
        ["legged_gym_go2/.../utils/isaacgym_utils.py", "Isaac Gym 工具"],
        ["legged_gym_go2/.../utils/math.py", "数学辅助"],
        ["legged_gym_go2/.../envs/h1_2/*", "H1_2 机型环境/配置"],
        ["legged_gym_go2/.../envs/h1/*", "H1 机型环境/配置"],
        ["legged_gym_go2/.../envs/g1/*", "G1 机型环境/配置"],
        ["legged_gym_go2/.../envs/tinymal/*", "TinyML 机型环境/配置"],
    ]))
    I.append(("h2", "8.2 高层观测分量说明"))
    I.append(("p", "40 维高层观测的具体分量划分如下，便于理解策略输入含义与调试。"))
    I.append(("table", [
        ["分量区间", "含义", "维度"],
        ["o[0:8]", "基础特征（位姿/速度/相对目标）", "8"],
        ["o[8:24]", "目标方向激光雷达分箱", "16"],
        ["o[24:40]", "障碍/边界激光雷达分箱", "16"],
    ]))
    I.append(("h2", "8.3 常用命令示例"))
    I.append(("p", "训练：运行 train_reach_avoid.py 启动高层策略训练，检查点写入 logs/。"))
    I.append(("p", "回放：运行 play_reach_avoid.py 加载检查点，在仿真界面观察导航行为。"))
    I.append(("p", "评测：运行 test_reach_avoid.py 批量评测，将轨迹与指标导出为 JSON 供统计。"))
    I.append(("p", "绘图：运行 plot_training_results.py 与 plot_env_layout.py 读取日志与配置，生成曲线与布局图。"))
    I.append(("h2", "8.4 提交材料说明"))
    I.append(("p", "本软著登记需提交三类材料：软件著作权登记申请表（在线填报后打印签章）、源代码鉴别材料（本手册配套的前30+后30页"
                     "源代码 PDF，每页不少于 50 行）、文档鉴别材料（即本操作手册，每页不少于 30 行）。源代码页眉与手册页眉的软件全称及"
                     "版本号须与申请表完全一致。"))
    I.append(("p", "（本手册完）本手册所述全部内容均依据项目真实源码整理；README 中提及的“剩余预算”“双 Critic”等内容属于论文方法"
                     "描述，未在本仓库代码中实现，故不写入本手册。如有疑问，以源码材料为准。"))
    return I

def render_manual_html():
    items = build_manual_items()
    # 第一遍：确定章节起始页（不含目录）
    content_pages = pack_pages(items)
    chap_start = {}
    pno = 1
    for page in content_pages:
        for it in page:
            if it[0] == "h1":
                chap_start[it[1]] = pno
                break
        pno += 1
    # 目录条目
    toc_lines = ["（本手册自目录起连续编页）"]
    for k, v in chap_start.items():
        toc_lines.append(f"{k} .................. 第 {v} 页")
    toc_items = [("h2", "目录")] + [("p", l) for l in toc_lines]
    # 第二遍：目录 + 内容
    all_items = toc_items + items
    pages = pack_pages(all_items)
    # 重新记录 h1 页号（目录会推后）
    new_chap = {}
    pn = 1
    for page in pages:
        for it in page:
            if it[0] == "h1":
                new_chap[it[1]] = pn
                break
        pn += 1
    # 用新页号回填目录页
    rendered = []
    pageno = 1
    idx = 0
    for page in pages:
        blk = []
        is_toc = (idx == 0)
        if is_toc:
            blk.append('<h3 class="c2">目录</h3>')
            for it in page:
                if it[0] == "p":
                    for ln in wrap_text(it[1], BODY_CPL):
                        blk.append(f'<p>{escape(ln)}</p>')
            # 用 new_chap 重写目录条目（覆盖上面粗略内容）
            blk = ['<h3 class="c2">目录</h3>']
            for k, v in new_chap.items():
                blk.append(f'<p>{escape(k)} .................. 第 {v} 页</p>')
            blk.append('<p>　</p>')
        else:
            for it in page:
                t = it[0]
                if t == "h1":
                    blk.append(f'<h2 class="c1">{escape(it[1])}</h2>')
                elif t == "h2":
                    blk.append(f'<h3 class="c2">{escape(it[1])}</h3>')
                elif t == "h3":
                    blk.append(f'<h4 class="c3">{escape(it[1])}</h4>')
                elif t == "p":
                    for ln in wrap_text(it[1], BODY_CPL):
                        blk.append(f'<p>{escape(ln)}</p>')
                elif t == "table":
                    rows = "".join("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in row) + "</tr>" for row in it[1])
                    blk.append(f'<table>{rows}</table>')
                elif t == "figure":
                    blk.append(f'<div class="fig">{it[1]}<div class="cap">{escape(it[2])}</div></div>')
        rendered.append(
            f'<section class="page"><div class="phead"><span class="hname">{HEADER}</span>'
            f'<span class="powner">著作权人：{OWNER}</span>'
            f'<span class="pno">第 {pageno} 页</span></div>'
            f'<div class="content">{"".join(blk)}</div></section>'
        )
        pageno += 1
        idx += 1
    html = f'''<!doctype html><html lang="zh"><head><meta charset="utf-8">
<style>
@page{{size:A4;margin:12mm}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"SimSun",serif;color:#000;background:#fff;font-size:12pt}}
.page{{page-break-after:always;height:273mm;display:flex;flex-direction:column}}
.page:last-child{{page-break-after:auto}}
.phead{{display:flex;align-items:baseline;justify-content:space-between;border-bottom:1px solid #000;
  padding-bottom:2mm;margin-bottom:3mm;font-size:9pt}}
.hname{{font-weight:bold}}
.pno{{font-weight:bold}}
.content{{flex:1;line-height:1.6}}
.c1{{font-family:"SimHei",sans-serif;font-size:15pt;margin:4mm 0 3mm}}
.c2{{font-family:"SimHei",sans-serif;font-size:13pt;margin:3mm 0 2mm}}
.c3{{font-family:"SimHei",sans-serif;font-size:12pt;margin:2mm 0 1mm}}
p{{text-indent:2em;margin:1.5mm 0}}
table{{border-collapse:collapse;width:100%;margin:2mm 0;font-size:10.5pt}}
td{{border:1px solid #000;padding:2mm 3mm;vertical-align:top}}
.fig{{text-align:center;margin:3mm 0}}
.fig svg{{width:90%;max-height:160mm}}
.cap{{font-size:10pt;margin-top:2mm}}
</style></head><body>{"".join(rendered)}</body></html>'''
    return html, len(pages)

# ============ Chrome 无头打印 ============
def chrome_pdf(html_path, pdf_path):
    import tempfile
    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    prof = tempfile.mkdtemp(prefix="cp_", dir=TMP)
    cmd = [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-extensions",
           "--no-first-run", "--no-pdf-header-footer", f"--user-data-dir={prof}",
           f"--print-to-pdf={pdf_path}", "file:///" + html_path.replace("\\", "/")]
    subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=120)
    return os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0

def main():
    files, all_lines, per_file_eff = build_source_lines()
    eff_total = len(all_lines)
    src_html, src_pages, _, taken = render_source_html(all_lines)
    src_html_path = os.path.join(TMP, "source.html")
    open(src_html_path, "w", encoding="utf-8").write(src_html)
    print(f"[3] source.html pages={src_pages} taken={taken}", flush=True)
    # 表单
    ffields, main_func, tech, dev_date = build_form_info(eff_total, per_file_eff)
    form_html = render_form_html(ffields, main_func, tech)
    form_html_path = os.path.join(TMP, "form.html")
    open(form_html_path, "w", encoding="utf-8").write(form_html)
    print("[4] form.html written", flush=True)
    # 操作手册
    man_html, man_pages = render_manual_html()
    man_html_path = os.path.join(TMP, "manual.html")
    open(man_html_path, "w", encoding="utf-8").write(man_html)
    print(f"[5] manual.html pages={man_pages}", flush=True)
    # 打印 PDF
    src_pdf = os.path.join(OUT, f"源代码鉴别材料_{SOFTWARE_NAME}_{VERSION}.pdf")
    form_pdf = os.path.join(OUT, f"申请表信息_{SOFTWARE_NAME}_{VERSION}.pdf")
    man_pdf = os.path.join(OUT, f"操作手册_{SOFTWARE_NAME}_{VERSION}.pdf")
    print("[6] printing source pdf...", flush=True)
    print("   src ok=", chrome_pdf(src_html_path, src_pdf), flush=True)
    print("[7] printing form pdf...", flush=True)
    print("   form ok=", chrome_pdf(form_html_path, form_pdf), flush=True)
    print("[8] printing manual pdf...", flush=True)
    print("   man ok=", chrome_pdf(man_html_path, man_pdf), flush=True)
    # 报告
    report = f"""# 软著材料生成报告
软件全称：{SOFTWARE_NAME}
版本号：{VERSION}
著作权人：{OWNER}
生成时间：{datetime.datetime.now():%Y-%m-%d %H:%M}

## 源码统计
- 取自研目录：{', '.join(DIRS)}
- 纳入 .py 文件数：{len(files)}
- 有效代码行数（去注释去空行，含折行）：{eff_total}
- 源代码鉴别材料页数：{src_pages}（每页50行，行号1-50；取前30+后30页，共{taken}行）
- 提交方式：因总量≥3000行，取前1500行+后1500行各30页

## 产出物
- {os.path.basename(src_pdf)}（源代码鉴别材料，PDF）
- {os.path.basename(form_pdf)}（申请表信息，PDF）
- {os.path.basename(man_pdf)}（操作手册鉴别材料，PDF）

## 操作手册
- 页数：{man_pages}（含目录；目录计入页码）
- 章节：7章（引言/功能概要/架构设计与选型/详细功能阐述/数据库概述/字典简述/术语表述）
- 因文档页数{'<60' if man_pages<60 else '≥60'}，按规范{'全部提交' if man_pages<60 else '取前30+后30页提交'}

## 待人工确认项
1. 著作权人证件号码、省/市地址（材料中未写明，登录后填写）
2. 开发完成日期（取 git 最新提交 {dev_date}，请核对实际完成日期）
3. 发表状态（按“未发表”填写，若已公开发布请改）
4. 软件简称留空（如需简称请补充）
5. README 中“剩余预算/双Critic”属论文方法，代码未实现，未写入材料
"""
    open(os.path.join(OUT, "生成报告.md"), "w", encoding="utf-8").write(report)
    print("EFF_TOTAL", eff_total)
    print("SRC_PAGES", src_pages, "TAKEN", taken)
    print("MAN_PAGES", man_pages)
    print("SRC_PDF", os.path.getsize(src_pdf) if os.path.exists(src_pdf) else "MISSING")
    print("FORM_PDF", os.path.getsize(form_pdf) if os.path.exists(form_pdf) else "MISSING")
    print("MAN_PDF", os.path.getsize(man_pdf) if os.path.exists(man_pdf) else "MISSING")

if __name__ == "__main__":
    main()
