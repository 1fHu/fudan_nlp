# CLAUDE.md — AI 驱动的 SOD 蛋白酶设计

> 本文件是项目的上下文文档，供 AI agent 或新成员快速接手。聚焦**项目背景**与**当前进展/结论**。

---

## 1. 项目目标（一句话）

用 AI **从头设计（de novo design）一种新型 SOD 酶**，使其既保留清除超氧自由基的催化功能，又能在微生物中表达分泌后**自组装为规整、稳定的晶体/纤维结构**，从而在体内长效发挥作用。

**要解决的痛点**：天然 SOD 作为药物时——
- 在体内扩散过快、被清除，难以富集到高效催化浓度；
- 易被体内蛋白酶降解，活性快速下降。

**核心科学问题**：AI 能否利用文献、数据库与生物学工具，主动挖掘天然自组装材料的特征，从头设计出兼具**高催化活性、结构稳定性、自组装能力**的新型功能蛋白。

---

## 2. 领域背景（必读，理解任务的化学前提）

### 2.1 为什么要做 SOD —— 自由基因果链
- 有氧呼吸时线粒体电子传递链偶尔"漏电"，生成**超氧阴离子自由基 O₂·⁻**（含未配对电子，反应性强）。
- O₂·⁻ 本身毒性中等，危险在下游：与 NO· 结合生成剧毒的**过氧亚硝酸盐 ONOO⁻**；在 Fe²⁺ 存在下经 **Fenton 反应**生成最强氧化剂之一 **·OH**（羟基自由基）。
- 因此需要在 O₂·⁻ 变坏前将其清除。

### 2.2 SOD 的催化机理（歧化反应）
$$2\,O_2^{·-} + 2H^+ \rightarrow H_2O_2 + O_2$$
- "歧化"：同一物质一半被氧化、一半被还原。一个 O₂·⁻ 交出电子被氧化为 O₂，另一个接收电子被还原为 H₂O₂。
- 靠**活性位点金属离子在两个氧化态间来回切换**实现（Cu²⁺↔Cu⁺ 或 Mn³⁺↔Mn²⁺），金属离子是稳定吞吐电子的中转站。

### 2.3 两大家族
- **Cu/Zn-SOD**：Cu 负责催化（换价），Zn 负责结构稳定。
- **Mn-SOD**（与 Fe-SOD 同源）：Mn 催化。

### 2.4 关键残基与结构概念
- **His（组氨酸）**：咪唑环氮原子配位金属，是抓住 Cu/Mn 的"手指"（例：His47/49/126 配位 Cu）。
- **Asp（天冬氨酸）**：带负电，参与配位。
- **Lys/Arg**：带正电，在表面形成**静电漏斗**，把带负电的底物 O₂·⁻ 导航进活性位点（SOD 催化逼近扩散极限的关键）。
- **active site（活性位点）**：金属 + 配位 His 构成的催化口袋。
- **β-barrel**：Cu/Zn-SOD 的核心折叠。
- **四级结构界面（interface）**：dimer/tetramer 中链与链的接触面，是自组装设计的目标，也是当前难点（见第 5 节）。

---

## 3. 系统架构：Agent Scaffold

整体是一条 **数据 → 结构特征 → 生成 → 验证** 的流水线，外层用 AI agent 编排专业工具。

```
①数据采集(SOD-Data-SDK) → ②结构挖掘(Agent-Env) → ③生成验证(Protein-Gen-Eva)
                                                         │
                              RFdiffusion3 → LigandMPNN → AlphaFold3 → 质检筛选
```

### ① SOD-Data-SDK（数据采集层）
- **目的**：构建干净的 SOD 目标池，作为后续挖掘的启动数据。
- **数据库**：Swiss-Prot（已湿实验验证）、UniProt（含自动生成条目，需筛选）。
- **字段**：Entry / Protein names / Organism / Length / Sequence / Cofactor。
- **筛选**：长度 100–250 AA；CD-HIT 相似度去冗余（暂定 95%）；AI 筛选。
- **工具**：
  - `CD-HIT` — 长度筛选 + Cofactor 补齐 + 去冗余。
  - `DIAMOND` — 蛋白-蛋白/核酸-蛋白比对、同源搜索、聚类；用于补齐缺失字段。
  - `CLEAN` — 预测 EC 酶编号（可对一条序列预测多个 EC 号，处理多功能酶），确认是否为 SOD。

### ② Agent-Env-Interaction（结构特征挖掘）
- **目标**：从头设计的酶必须满足现有 SOD 的结构与分子动力学特性。
- **挖掘维度**：
  1. 活性位点与静电漏斗（PyMOL + APBS 算静电、Lys/Arg 分布保守性、电荷密度）；
  2. 配位相关残基（His 与金属的配位）；
  3. 残基带电情况；
  4. 主链/侧链原子坐标（CIF）；
  5. 侧链二面角（电荷取向）。
- **聚类**：对池中所有 SOD 计算上述维度后聚类，聚类结果代表真实酶的特性，**作为 RFD 生成骨架后的强约束验证**。
- **筛选**：选代表性酶做 MD 模拟，得到动态稳定的酶。
- **技术路线**：`agent + memory + env → trajectory + report`；PyMOL 沙盒 + AI agent 闭环，自主跑命令、存 log、实时截图、按需读 log 选参数。

### ③ Protein-Gen-Eva（生成-验证流水线）
- `RFdiffusion3 (RFD3)` — 在固定 motif（如 His47/49/126）约束下，生成包裹金属离子的 3D 骨架。全原子建模，可感知配体/金属/DNA；**只产骨架，不定序列**。
- `LigandMPNN` — 感知金属配体环境，在骨架上做 inverse folding 填充最优序列，同时锁定配位残基不变。
- `AlphaFold3 (AF3)` — 多 seed、多 recycle 重折叠验证，按 pLDDT / PAE 筛高置信度设计。

### 质检指标定义
- **pLDDT**（0–100，逐残基置信度）：高 = 该处结构可信。
- **PAE**（Predicted Aligned Error）：残基对相对位置误差，低 = 结构域相对摆放可信。
- **RMSD**（Å，结构叠合后原子平均偏差）：**<1.0 优秀；>2.0 剔除**。
- ⚠️ **pLDDT/PAE 只反映折叠置信度，不反映物理可行性**——必须叠加几何检查（见第 5 节）。

---

## 4. 核心设计接口（RFD 输入示例）

```json
{
  "cu_sod_active_site_design": {
    "input": "cu_sod_active_site.pdb",
    "contig": "30-50,A47,5-10,A49,20-40,A126,30-50",
    "ligand": "CU",
    "unindex": "A47,A49,A126",
    "select_fixed_atoms": {
      "A47": "ND1,CG,CE1,NE2,CD2,CB",
      "A49": "NE2,CG,CE1,ND1,CD2,CB",
      "A126": "NE2,CG,CE1,ND1,CD2,CB"
    },
    "select_hotspots": "A47,A49,A126",
    "select_buried": "A47,A49,A126",
    "length": "120-180"
  }
}
```

字段说明：
- `contig`：交替描述"新生成段（如 30-50）"与"固定 motif 残基（A47/A49/A126）"。
- `ligand: CU`：口袋内要包一个铜离子，骨架须避免与之碰撞并形成有利配位。
- `select_fixed_atoms`：精确到原子名锁定 His 侧链；`ND1`、`NE2` 是咪唑环上配位金属的两个氮。
- `select_hotspots` / `select_buried`：三个配位 His 设为热点且埋藏。
- `length`：目标蛋白总长。

> 注：实验脚本中也使用 RFdiffusion 标准的 `contigmap.contigs=[10-30/A19-45/...]`（斜杠语法）。两套写法对应不同入口，注意区分。

---

## 5. 当前进展与关键结论（实验记录，最重要）

> 难点：不仅要设计单个酶，还要设计链间**界面**与**对称组装**以实现自组装。界面残基不在 motif 内，RFD 默认不知道其存在。

**TL;DR**：用 RFD 直接设计 SOD 界面/对称体目前不可靠；**若天然界面已足够好，直接用 MPNN 重设计序列，可用率 >0.85（以 `6D52` 为例）。**

### 路 A：C2 对称 de novo 设计（最具创新性）
- 思路：把活性位点当 motif，让 RFD 设计全新对称二聚体。
- **结果失败**：两条链在 3D 中物理穿插碰撞——链间最近骨架原子 0.79 Å（应 ≥3.5 Å）；34 对原子 <2 Å（实际 clash）；两 Mn 中心仅 9.35 Å（天然约 18–25 Å）。湿实验无法折叠、MD 会爆。
- **教训**：PyMOL 配色看着"井然有序"、pLDDT 高，但只反映折叠置信度。**pLDDT 不能单独作为二聚体质量判据**。

### 路 B：partial diffusion（保留天然骨架，只重塑界面）
- **结果失败**：`partial_T` 偏大破坏 motif 几何（Mn-Mn 从天然 19.4 → 13.31 Å）；RFD 该步只产骨架，输出 194 个残基全为 GLY（polyG）+ 锁定位 HIS/ASP；`trb` 中 motif 未被当约束处理；两链不对称漂移。
- **结论**：partial diffusion 不适合此任务。

### 实用结论
- 天然界面够好（如 `6D52`）→ **跳过 RFD，直接 MPNN 重设计序列**，可用率 >0.85。
- 质量门槛：align RMSD <1.0 Å 可用；>2.0 Å 剔除（说明 partial_T 过大破坏了 motif）。

### 质检红线（务必双重把关）
1. 结构置信度：pLDDT / PAE。
2. 物理几何：链间碰撞（PyMOL `find_pairs`）、金属-金属间距、口袋对称性。
- **只看 pLDDT 必被误导。**

---

## 6. 工具清单

| 工具 | 用途 | 仓库 |
|---|---|---|
| CD-HIT | 序列去冗余、长度筛选 | github.com/weizhongli/cdhit |
| DIAMOND | 同源搜索、补字段 | github.com/bbuchfink/diamond |
| CLEAN | EC 酶编号预测 | github.com/tttianhao/CLEAN |
| RFdiffusion3 / RFdiffusionAA | 全原子/配体感知骨架生成 | RoseTTAFold 系列 |
| LigandMPNN | 配体感知 inverse folding 序列设计 | Baker Lab |
| AlphaFold3 | 折叠验证（pLDDT/PAE） | — |
| PyMOL + APBS | 结构分析、静电、几何质检 | — |

---

## 7. 参考文献
- RFdiffusion — Watson et al., 2023, *Nature*.
- ProteinMPNN — Dauparas et al., 2022, *Science*.
- RoseTTAFold All-Atom / RFdiffusionAA — Krishna et al., 2024, *Science*.
- AlphaFold3 — Abramson et al., 2024, *Nature*.
- RFdiffusion3 — 2025, *bioRxiv*（全原子生物分子相互作用设计）。
- CLEAN — Yu et al., 2023, *Science*（酶功能预测）。

---

## 8. 展望 / 待办
- 任务泛化：从单一 SOD 扩展到多种蛋白质的从头设计。
- 工程化：构建 harness，更高效地编排专业工具与数据库。
- 参考平台：openbio.tech、biomni.stanford.edu。

---

## 9. 关键约定 / Gotchas（速查）
- RFD 只产骨架，序列必须交给 (Ligand)MPNN。
- `partial_T` 过大 → 破坏 motif 几何，剔除。
- 质检 = 结构置信度 + 物理几何，缺一不可。
- 天然界面好 → 优先直接 MPNN，别盲目上 RFD。
- 金属配位原子名：His 的 `ND1` / `NE2` 是配位氮。
