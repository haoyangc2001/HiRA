# -*- coding: utf-8 -*-
import os, sys, time
sys.path.insert(0, r"D:\repository\Go2HierarchicalReachAvoidRL\output\copyright_materials")
import gen
LOG = open(r"D:\repository\Go2HierarchicalReachAvoidRL\output\copyright_materials\gen_html.log", "w", encoding="utf-8")
def L(m):
    LOG.write(m + "\n"); LOG.flush()
TMP = gen.TMP
L("start build_source_lines")
t = time.time()
files, all_lines, eff = gen.build_source_lines()
L(f"build_source_lines done eff={len(all_lines)} files={len(files)} {round(time.time()-t,2)}s")
t = time.time()
src_html, src_pages, _, taken = gen.render_source_html(all_lines)
open(os.path.join(TMP, "source.html"), "w", encoding="utf-8").write(src_html)
L(f"source.html done pages={src_pages} taken={taken} {round(time.time()-t,2)}s")
t = time.time()
ff, mf, tech, dd = gen.build_form_info(len(all_lines), eff)
L(f"build_form_info done dev_date={dd} {round(time.time()-t,2)}s")
t = time.time()
form_html = gen.render_form_html(ff, mf, tech)
open(os.path.join(TMP, "form.html"), "w", encoding="utf-8").write(form_html)
L(f"form.html done {round(time.time()-t,2)}s")
t = time.time()
man_html, man_pages = gen.render_manual_html()
open(os.path.join(TMP, "manual.html"), "w", encoding="utf-8").write(man_html)
L(f"manual.html done pages={man_pages} {round(time.time()-t,2)}s")
for n in ("source.html", "form.html", "manual.html"):
    p = os.path.join(TMP, n)
    L(f"{n} {os.path.getsize(p)} bytes")
L("ALL DONE")
LOG.close()
