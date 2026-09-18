# -*- coding: utf-8 -*-
import os, sys, time, io, tokenize
sys.path.insert(0, r"D:\repository\Go2HierarchicalReachAvoidRL\output\copyright_materials")
import gen

ROOT = gen.ROOT
log = open(r"D:\repository\Go2HierarchicalReachAvoidRL\output\copyright_materials\diag.log", "w", encoding="utf-8")
files = gen.collect_files()
log.write(f"files={len(files)}\n"); log.flush()
for rel in files:
    p = os.path.join(ROOT, rel)
    try:
        src = open(p, encoding="utf-8", errors="ignore").read()
    except Exception as e:
        log.write(f"READERR {rel} {e}\n"); log.flush(); continue
    t = time.time()
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
        n = sum(1 for tk in toks if tk.type != tokenize.ENCODING and tk.type != tokenize.NL and tk.type != tokenize.NEWLINE and tk.type != tokenize.ENDMARKER)
        log.write(f"OK {rel} toks={n} {round(time.time()-t,3)}s\n")
    except Exception as e:
        log.write(f"TOKERR {rel} {type(e).__name__} {round(time.time()-t,3)}s\n")
    log.flush()
log.write("DONE\n"); log.flush()
log.close()
print("DIAG DONE")
