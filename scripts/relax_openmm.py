#!/usr/bin/env python3
"""
方案 B —— OpenMM 能量最小化去 clash（后处理松弛）。

对应「碰撞优化方案.md」方案 B：在不破坏整体折叠与 motif 几何的前提下，用物理力场
把轻度 steric clash 松弛掉。对【骨架严重穿插】(bb_min<1Å) 救不回来——那类必须靠方案 A
从生成阶段解决；本脚本用于 MPNN 填序列后的全原子模型，或几何尚可、仅局部 clash 的结构。

流程:
  PDBFixer 补全缺失重原子+加氢 -> amber14 力场建系 -> 对 N/CA/C/CB 加谐振子约束
  -> L-BFGS 能量最小化 -> 输出 minimized.pdb，并打印松弛前后 clash 对比。

依赖: openmm, pdbfixer  (本地无 GPU 也能在 CPU 平台跑；集群同样可用)
  conda: conda install -c conda-forge openmm pdbfixer
  pip  : pip install openmm pdbfixer   # 视 Python 版本是否有 wheel

用法:
  python scripts/relax_openmm.py in.pdb -o out.pdb
  python scripts/relax_openmm.py in.pdb -o out.pdb --restraint-k 800 --max-iter 2000
"""
from __future__ import annotations
import argparse, sys

RESTRAINED = {"N", "CA", "C", "CB"}  # 受约束的骨架原子（保护折叠 + motif）


def count_interchain_clashes(pdb_path, cutoff=2.0):
    """复用与 geom_qc 一致的口径：链间重原子(<cutoff Å) 对数 + 最近骨架距离。"""
    import numpy as np
    bb = {"N", "CA", "C", "O"}
    chains = {}
    with open(pdb_path) as fh:
        for ln in fh:
            if ln[:6].strip() not in ("ATOM", "HETATM"):
                continue
            try:
                xyz = np.array([float(ln[30:38]), float(ln[38:46]), float(ln[46:54])])
            except ValueError:
                continue
            elem = (ln[76:78].strip() or ln[12:16].strip()[:1]).upper()
            ch = ln[21].strip() or "A"
            chains.setdefault(ch, {"all": [], "bb": []})
            if elem != "H":
                chains[ch]["all"].append(xyz)
            if ln[12:16].strip() in bb:
                chains[ch]["bb"].append(xyz)
    keys = sorted(chains)
    clash, bbmin = 0, float("inf")
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a = np.array(chains[keys[i]]["all"]); b = np.array(chains[keys[j]]["all"])
            if len(a) and len(b):
                d = np.linalg.norm(a[:, None] - b[None], axis=-1)
                clash += int((d < cutoff).sum())
            a = np.array(chains[keys[i]]["bb"]); b = np.array(chains[keys[j]]["bb"])
            if len(a) and len(b):
                bbmin = min(bbmin, float(np.linalg.norm(a[:, None] - b[None], axis=-1).min()))
    return clash, bbmin


def relax(in_pdb, out_pdb, restraint_k=800.0, max_iter=0, implicit=True):
    from openmm import app, unit, CustomExternalForce, LangevinIntegrator, Platform
    from pdbfixer import PDBFixer

    # 1) 补全结构（缺失重原子 / 氢）
    fixer = PDBFixer(filename=in_pdb)
    fixer.findMissingResidues()
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(7.0)

    # 2) 建系：amber14 + (可选)GBn2 隐式溶剂
    ff_files = ["amber14-all.xml"]
    ff_files.append("implicit/gbn2.xml" if implicit else "amber14/tip3pfb.xml")
    forcefield = app.ForceField(*ff_files)
    modeller = app.Modeller(fixer.topology, fixer.positions)
    system = forcefield.createSystem(
        modeller.topology, nonbondedMethod=app.CutoffNonPeriodic,
        nonbondedCutoff=1.0 * unit.nanometer, constraints=app.HBonds,
    )

    # 3) 对 N/CA/C/CB 加谐振子约束，锁住整体折叠与 motif
    restraint = CustomExternalForce("0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
    restraint.addGlobalParameter("k", restraint_k * unit.kilojoule_per_mole / unit.nanometer**2)
    for p in ("x0", "y0", "z0"):
        restraint.addPerParticleParameter(p)
    n_restrained = 0
    for atom in modeller.topology.atoms():
        if atom.name in RESTRAINED:
            pos = modeller.positions[atom.index]
            restraint.addParticle(atom.index, [pos.x, pos.y, pos.z])
            n_restrained += 1
    system.addForce(restraint)

    # 4) 最小化
    integrator = LangevinIntegrator(300 * unit.kelvin, 1 / unit.picosecond, 0.002 * unit.picoseconds)
    try:
        platform = Platform.getPlatformByName("CUDA")
    except Exception:
        try:
            platform = Platform.getPlatformByName("CPU")
        except Exception:
            platform = None
    sim = app.Simulation(modeller.topology, system, integrator, platform)
    sim.context.setPositions(modeller.positions)

    e0 = sim.context.getState(getEnergy=True).getPotentialEnergy()
    sim.minimizeEnergy(maxIterations=max_iter)  # 0 = 跑到收敛
    e1 = sim.context.getState(getEnergy=True).getPotentialEnergy()

    positions = sim.context.getState(getPositions=True).getPositions()
    with open(out_pdb, "w") as fh:
        app.PDBFile.writeFile(modeller.topology, positions, fh, keepIds=True)

    return n_restrained, e0, e1


def main():
    ap = argparse.ArgumentParser(description="OpenMM 约束能量最小化去 clash")
    ap.add_argument("in_pdb")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--restraint-k", type=float, default=800.0,
                    help="骨架谐振子力常数 kJ/mol/nm^2 (默认 800，越大越保形)")
    ap.add_argument("--max-iter", type=int, default=0, help="0=跑到收敛")
    ap.add_argument("--explicit", action="store_true", help="用显式水(默认隐式 GBn2)")
    args = ap.parse_args()

    c0, bb0 = count_interchain_clashes(args.in_pdb)
    print(f"[before] inter-chain clash(<2Å)={c0}  bb_min={bb0:.2f} Å")
    if bb0 < 1.0:
        print("⚠️  bb_min<1Å：深度穿插，松弛大概率救不回，建议改走方案 A 重新生成。")

    try:
        n, e0, e1 = relax(args.in_pdb, args.out, args.restraint_k, args.max_iter,
                          implicit=not args.explicit)
    except ImportError as e:
        sys.exit(f"缺少依赖: {e}\n请先: conda install -c conda-forge openmm pdbfixer")

    c1, bb1 = count_interchain_clashes(args.out)
    print(f"[after ] inter-chain clash(<2Å)={c1}  bb_min={bb1:.2f} Å")
    print(f"约束原子(N/CA/C/CB)={n}  能量 {e0} -> {e1}")
    print(f"clash {c0}->{c1}  ({'改善' if c1 < c0 else '未改善'})  输出: {args.out}")


if __name__ == "__main__":
    main()
