# -*- coding: utf-8 -*-
import os, sys, io, tokenize, time
sys.path.insert(0, r"D:\repository\Go2HierarchicalReachAvoidRL\output\copyright_materials")
import gen
ROOT = gen.ROOT
LOG = open(r"D:\repository\Go2HierarchicalReachAvoidRL\output\copyright_materials\test_bsl.log", "w", encoding="utf-8")
def strip_comments(src):
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except Exception:
        return [l.rstrip() for l in src.splitlines() if l.strip()]
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
    if len(line) <= limit:
        return [line]
    res = []
    cur = line
    guard = 0
    while len(cur) > limit:
        guard += 1
        if guard > 10000:
            LOG.write("WRAP_GUARD_TRIP line="+repr(line[:120])+"\n"); LOG.flush(); return res + [cur]
        sp = cur.rfind(" ", 0, limit)
        if sp <= 0:
            sp = limit
        res.append(cur[:sp].rstrip())
        cur = "    " + cur[sp:].lstrip()
    res.append(cur)
    return res
files = gen.collect_files()
all_lines = []
for rel in files:
    p = os.path.join(ROOT, rel)
    src = open(p, encoding="utf-8", errors="ignore").read()
    eff = strip_comments(src)
    t = time.time()
    n = 0
    for code in eff:
        for wl in wrap_line(code):
            all_lines.append((rel, wl))
            n += 1
    LOG.write(f"{rel} eff={len(eff)} lines={n} {round(time.time()-t,3)}s\n"); LOG.flush()
LOG.write(f"TOTAL {len(all_lines)}\n"); LOG.close()
