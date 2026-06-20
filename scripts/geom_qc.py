#!/usr/bin/env python3
"""
geom_qc.py — 几何质检 / 碰撞(clash)量化，对应「碰撞优化方案.md」第 1 节红线。

仅依赖 numpy（无需 PyMOL / biotite），可直接跑在已有的 RFD 设计 PDB 上。

计算每个 PDB：
  1. 链间最近骨架原子距离 (N,CA,C,O)          红线: >= 3.5 Å
  2. 链间 clash 原子对数 (heavy atom < 2.0 Å)   红线: == 0
  3. 活性中心间距:
       - 若有金属 HETATM (MN/CU/ZN/FE) -> 金属-金属距离
       - 否则用每条链 HIS 配位氮(NE2/ND1) 质心作代理
     红线: 落在天然区间 (默认 Mn-SOD 18-25 Å, 可调)

用法:
  单文件:   python scripts/geom_qc.py path/to/design.pdb
  批量目录: python scripts/geom_qc.py rfd_c2_design --glob '**/*.pdb' --csv qc_report.csv
"""
from __future__ import annotations
import argparse, glob, os, sys
import numpy as np

BACKBONE = {"N", "CA", "C", "O"}
METALS = {"MN", "CU", "ZN", "FE"}
HIS_COORD_N = {"NE2", "ND1"}

# 红线阈值（可通过命令行覆盖）
MIN_INTERCHAIN_BB = 3.5      # Å
CLASH_CUTOFF = 2.0           # Å
ACTIVE_SITE_LO = 18.0        # Å
ACTIVE_SITE_HI = 25.0        # Å


def parse_pdb(path):
    """返回 list[dict]: 每个原子 {chain, resn, resi, atom, elem, xyz, hetatm}."""
    atoms = []
    with open(path) as fh:
        for ln in fh:
            rec = ln[:6].strip()
            if rec not in ("ATOM", "HETATM"):
                continue
            try:
                x = float(ln[30:38]); y = float(ln[38:46]); z = float(ln[46:54])
            except ValueError:
                continue
            atom = ln[12:16].strip()
            elem = ln[76:78].strip().upper()
            if not elem:  # 老式 PDB 无 element 列，从原子名推断
                elem = "".join(c for c in atom if c.isalpha())[:1].upper()
            atoms.append(dict(
                chain=ln[21].strip() or "A",
                resn=ln[17:20].strip(),
                resi=ln[22:26].strip(),
                atom=atom, elem=elem,
                xyz=np.array([x, y, z]),
                hetatm=(rec == "HETATM"),
            ))
    return atoms


def by_chain(atoms):
    chains = {}
    for a in atoms:
        chains.setdefault(a["chain"], []).append(a)
    return chains


def min_interchain_backbone(chains):
    """两两链之间，骨架原子的最小距离。返回 (dist, chainpair)."""
    keys = sorted(chains)
    best = (np.inf, None)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            ca = np.array([a["xyz"] for a in chains[keys[i]] if a["atom"] in BACKBONE])
            cb = np.array([a["xyz"] for a in chains[keys[j]] if a["atom"] in BACKBONE])
            if len(ca) == 0 or len(cb) == 0:
                continue
            d = np.linalg.norm(ca[:, None, :] - cb[None, :, :], axis=-1)
            m = d.min()
            if m < best[0]:
                best = (m, f"{keys[i]}-{keys[j]}")
    return best


def count_clashes(chains, cutoff=CLASH_CUTOFF):
    """链间重原子(非 H) 距离 < cutoff 的原子对数（所有链对求和）。"""
    keys = sorted(chains)
    total = 0
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            ca = np.array([a["xyz"] for a in chains[keys[i]] if a["elem"] != "H"])
            cb = np.array([a["xyz"] for a in chains[keys[j]] if a["elem"] != "H"])
            if len(ca) == 0 or len(cb) == 0:
                continue
            d = np.linalg.norm(ca[:, None, :] - cb[None, :, :], axis=-1)
            total += int((d < cutoff).sum())
    return total


def active_site_separation(atoms, chains):
    """有金属 -> 金属-金属距离; 否则 HIS 配位氮质心代理。返回 (dist, mode)."""
    metals = [a for a in atoms if a["hetatm"] and a["resn"] in METALS]
    if len(metals) >= 2:
        pts = [m["xyz"] for m in metals]
        # 取相距最远的两个金属（dimer 的两个活性中心）
        best = 0.0
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                best = max(best, float(np.linalg.norm(pts[i] - pts[j])))
        return best, "metal-metal"
    # 代理：每条链 HIS 配位氮(NE2/ND1)质心；骨架-only 输出无侧链时退回 HIS CA 质心
    cents, mode = {}, "HIS-Nz(proxy)"
    for ch, al in chains.items():
        ns = [a["xyz"] for a in al if a["resn"] == "HIS" and a["atom"] in HIS_COORD_N]
        if ns:
            cents[ch] = np.mean(ns, axis=0)
    if len(cents) < 2:  # 退回 CA
        cents, mode = {}, "HIS-CA(proxy)"
        for ch, al in chains.items():
            ns = [a["xyz"] for a in al if a["resn"] == "HIS" and a["atom"] == "CA"]
            if ns:
                cents[ch] = np.mean(ns, axis=0)
    if len(cents) >= 2:
        ks = sorted(cents)
        return float(np.linalg.norm(cents[ks[0]] - cents[ks[1]])), mode
    return float("nan"), "n/a"


def evaluate(path, args):
    atoms = parse_pdb(path)
    chains = by_chain(atoms)
    bb_min, pair = min_interchain_backbone(chains)
    clashes = count_clashes(chains, args.clash_cutoff)
    asep, mode = active_site_separation(atoms, chains)

    pass_bb = bb_min >= args.min_bb
    pass_clash = clashes == 0
    pass_as = (not np.isnan(asep)) and (args.as_lo <= asep <= args.as_hi)
    ok = pass_bb and pass_clash and pass_as
    return dict(path=path, nchains=len(chains), bb_min=bb_min, clash=clashes,
                asep=asep, asep_mode=mode, pass_bb=pass_bb, pass_clash=pass_clash,
                pass_as=pass_as, ok=ok)


def main():
    ap = argparse.ArgumentParser(description="几何质检 / clash 量化")
    ap.add_argument("target", help="PDB 文件或目录")
    ap.add_argument("--glob", default="**/*.pdb", help="目录模式下的匹配 (默认 **/*.pdb)")
    ap.add_argument("--csv", help="把结果写到 CSV")
    ap.add_argument("--min-bb", type=float, default=MIN_INTERCHAIN_BB)
    ap.add_argument("--clash-cutoff", type=float, default=CLASH_CUTOFF)
    ap.add_argument("--as-lo", type=float, default=ACTIVE_SITE_LO)
    ap.add_argument("--as-hi", type=float, default=ACTIVE_SITE_HI)
    args = ap.parse_args()

    if os.path.isdir(args.target):
        files = sorted(glob.glob(os.path.join(args.target, args.glob), recursive=True))
    else:
        files = [args.target]
    if not files:
        sys.exit(f"未找到 PDB: {args.target}")

    rows = []
    hdr = f"{'design':52} {'ch':>2} {'bb_min':>7} {'clash':>6} {'a-site':>7} {'mode':>20} {'PASS':>5}"
    print(hdr); print("-" * len(hdr))
    for f in files:
        r = evaluate(f, args)
        rows.append(r)
        name = os.path.relpath(f, args.target if os.path.isdir(args.target) else ".")
        asep = f"{r['asep']:.2f}" if not np.isnan(r['asep']) else "nan"
        flag = "OK" if r["ok"] else "FAIL"
        print(f"{name[-52:]:52} {r['nchains']:>2} {r['bb_min']:>7.2f} "
              f"{r['clash']:>6} {asep:>7} {r['asep_mode']:>20} {flag:>5}")

    n_ok = sum(r["ok"] for r in rows)
    print("-" * len(hdr))
    print(f"汇总: {n_ok}/{len(rows)} 通过全部红线 "
          f"(bb>={args.min_bb}Å, clash=0, a-site {args.as_lo}-{args.as_hi}Å)")

    if args.csv:
        import csv
        with open(args.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print(f"CSV 已写入: {args.csv}")


if __name__ == "__main__":
    main()
