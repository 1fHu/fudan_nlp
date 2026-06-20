#!/bin/bash
# =============================================================================
# 方案 A —— RFdiffusion C2 对称引导势(guiding potentials)参数网格扫描
# 目标：通过加强链间接触势 / ROG 约束，压下「碰撞优化方案.md」里记录的链间穿插
#       (6qv9: bb_min 0.79 Å, 34 对 clash, 两 Mn 中心 9.35 Å)。
#
# 在【远程 GPU 集群】运行（本地 Mac 无 GPU）。
# 网格: guide_scale ∈ {2,3,4,5} × weight_inter ∈ {0.1,0.3,0.5,1.0}
#       × guide_decay ∈ {quadratic, linear}  = 32 组，每组 num_designs 个。
# 每组结果落到独立目录，跑完后用 scripts/geom_qc.py 过几何红线即可对比。
# =============================================================================
set -euo pipefail

# ===== 路径配置（按集群实际修改）=====
RFDIFF_DIR=${RFDIFF_DIR:-/mnt/shared-storage-gpfs2/yangyajie-gpfs02/RFdiffusion}
INPUT_PDB=${INPUT_PDB:-$RFDIFF_DIR/input/6qv9_chainA_clean.pdb}
OUTPUT_ROOT=${OUTPUT_ROOT:-$RFDIFF_DIR/outputs/6qv9_potential_sweep}
CKPT=${CKPT:-$RFDIFF_DIR/models/Base_ckpt.pt}

# ===== 生成参数 =====
NUM_DESIGNS=${NUM_DESIGNS:-10}          # 每组先 10 个看趋势，定下最优组再放大
# motif contig：固定三段含配位残基的二级结构（与记录一致），两端/linker 留生成段
CONTIGS=${CONTIGS:-'[20-20/A19-45/30-30/A66-89/30-30/A153-173/20-20]'}

# ===== 扫描网格 =====
GUIDE_SCALES=(2 3 4 5)
WEIGHT_INTERS=(0.1 0.3 0.5 1.0)
GUIDE_DECAYS=(quadratic linear)
WEIGHT_INTRA=1                          # 链内接触势固定

mkdir -p "$OUTPUT_ROOT"
SUMMARY="$OUTPUT_ROOT/sweep_index.tsv"
printf "run_id\tguide_scale\tweight_inter\tguide_decay\toutdir\n" > "$SUMMARY"

run_one () {
    local gs=$1 wi=$2 gd=$3
    local rid="gs${gs}_wi${wi}_${gd}"
    local outdir="$OUTPUT_ROOT/$rid"
    mkdir -p "$outdir"
    echo ">>> [$rid] guide_scale=$gs weight_inter=$wi guide_decay=$gd"

    HYDRA_FULL_ERROR=1 python "$RFDIFF_DIR/scripts/run_inference.py" \
        --config-name symmetry \
        inference.input_pdb="$INPUT_PDB" \
        inference.output_prefix="$outdir/design" \
        inference.num_designs="$NUM_DESIGNS" \
        inference.ckpt_override_path="$CKPT" \
        inference.symmetry=c2 \
        "contigmap.contigs=$CONTIGS" \
        potentials.olig_intra_all=True \
        potentials.olig_inter_all=True \
        "potentials.guiding_potentials=[\"type:olig_contacts,weight_intra:${WEIGHT_INTRA},weight_inter:${wi}\"]" \
        potentials.guide_scale="$gs" \
        potentials.guide_decay="$gd" \
        2>&1 | tee "$outdir/run.log"

    printf "%s\t%s\t%s\t%s\t%s\n" "$rid" "$gs" "$wi" "$gd" "$outdir" >> "$SUMMARY"
}

# ===== 主循环 =====
for gs in "${GUIDE_SCALES[@]}"; do
  for wi in "${WEIGHT_INTERS[@]}"; do
    for gd in "${GUIDE_DECAYS[@]}"; do
      run_one "$gs" "$wi" "$gd"
    done
  done
done

echo
echo "=== 扫描完成。索引: $SUMMARY ==="
echo "下一步几何质检（在装了 numpy 的环境）："
echo "  python scripts/geom_qc.py $OUTPUT_ROOT --glob '**/design_*.pdb' --csv $OUTPUT_ROOT/qc_sweep.csv"
echo "然后挑 bb_min>=3.5Å & clash=0 & a-site 18-25Å 的参数组放大 num_designs。"
