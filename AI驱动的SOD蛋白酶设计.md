# AI驱动的SOD蛋白酶设计

> ![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NGUxNzA2ZTc5YzZiODFkZWU2NjBiNWIzNjYxZWZlMmZfMjc5NmEwYWVkYTlkOWM2YmJlYjdhNTZjZmNmNmIwMmRfSUQ6NzYyMzQzNzA0MTY2OTMxMTQyMF8xNzgxOTQxNTE4OjE3ODIwMjc5MThfVjM)
> 
> 

# 任务描述

## 问题描述

- **自由基（Free Radical）**：它是指**含有至少一个未配对电子的原子或分子，O₂·⁻**是细胞线粒体有氧呼吸时产生的副产物，是一种自由基。虽然本身毒性中等，但它会和NO·结合生成剧毒的过氧亚硝酸盐（ONOO⁻），也可以在铁存在时间接引发Fenton反应产生·OH。

---

- **SOD 酶：**是一种含有金属离子的蛋白酶，它的活性位点有一个金属离子（Cu²⁺/Zn²⁺ 或 Mn²⁺），通过交替的氧化还原循环，把两个 O₂·⁻ 转化成 H₂O₂ 和 O₂，相当于用酶活性位点代替自由基去"接收"那个多余的电子，安全地中止链式反应的第一步。但是**天然分泌物**体内**迅速扩散清除**，难以**富集达到高效的催化浓度，且**易被体内**蛋白酶降解**，使其活性下降。

---

- **科学问题：AI能否利用丰富的文献，数据库以及生物学工具主动挖掘出天然自组装材料的特征**，从头设计一类**新型蛋白，**利用基因工程在**活体材料或微生物中表达功能蛋白**（如酶、细胞因子），**使得微生物分泌后能迅速自组装为****具备规整结构、高催化活性和稳定性的**的蛋白晶体，在体内发挥稳定且长效的生物功能。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OTc4ZGRlYzY2YzMxNTQ0OWQ3NzQ0Nzg2NDhhMTI2ZjdfYjEzY2ZiZGZkNTc1YTcyN2JiNWIwYmQ1MDMyODNjY2VfSUQ6NzYyMzQ0MDc5NzAyNjk0NjI2NV8xNzgxOTQxNTE4OjE3ODIwMjc5MThfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTkyMTExNTBiMDE3ZjQyNmNlYTQ4M2RiYzkxNmVjZDlfYzBkZTc0OGE5ZmE2OWNlZmRlZWE2NzNmMWEwMGE4YTVfSUQ6NzYyMzQzNzQ0NTA3NzcxNjE0Nl8xNzgxOTQxNTE4OjE3ODIwMjc5MThfVjM)

## 研究者面临的困境 

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTI0NTgxNjY3ZDQwY2U2NjMxYWRkOGE4YjFmMWJmNTBfMmRhYmM4N2Y2MjYxZjlmZWNkNjAzN2RlYTU0YWU3NzhfSUQ6NzYyMzQzNjEyNzkyMzcxOTEyMl8xNzgxOTQxNTE4OjE3ODIwMjc5MThfVjM)

## Researcher给出的可参考流程

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MzkyM2IyOTk1MWNjMmIzY2JhYzU1YjlhY2RmYjJkNWJfOGMyNjZlZDk3NzJkMDY3ODQ2NzE0ZWI0Zjc1NTUzYWVfSUQ6NzYyMzQ0MzAwODU5NTI2NjUxM18xNzgxOTQxNTE4OjE3ODIwMjc5MThfVjM)



# Agent Scaffold 实施细节

## SOD\-Data\-SDK   

### SOD酶目标池构建

1. **目的**：作为后续数据挖掘的启动数据，类似基础的数据采集 SDK

2. **数据库**：Swiss\-Prot\(经过湿实验验证\)、Uniprot  

```Plain Text
Entry：唯一标识
Protein names：蛋白质名称
Organism：存在的细菌名称
Length：氨基酸个数
Sequence：氨基酸序列
Cofactor：活性因子
```

如下数据样例：

3. **TODO数据筛选**：对未经验证的Uniprot需要进行精细化筛选

    1. 筛选原因：Uniprot有些数据item是自动化生成的，所以需要验证。

    2. 筛选角度：

        - *长度筛选（100AA—250AA）**；*

        - *相似性合并（借用工具CD\-HIT，相似度高的进行去冗余，暂定95%）**；*

        - *AI筛选 *

4. **AI\-Toolset**

|工具名称|具体解决的任务|github|环境API|
|---|---|---|---|
|**cdhit**|对候选集合做**“长度筛选 \+ Cofactor 补齐 \+ CD\-HIT 去冗余”操作**<br>|https://github\.com/weizhongli/cdhit/tree/master|作为Agent数据处理的工具，用于完成大规模蛋白质数据集\(eg\.UniProt\)的初筛/去冗余<br>|
|**diamond**|通过进行**蛋白\-蛋白序列、核酸\-蛋白比对或同源搜索以及蛋白聚类任务**|https://github\.com/bbuchfink/diamond <br>|作为Agent数据处理的工具，依据同源搜索能力用于填充缺失字段值<br>|
|**CLEAN**|**解决蛋白质功能注释的准确性问题，用于多功能酶的识别问题**能够为同一条蛋白质序列同时预测多个 EC 编号，解决了传统方法难以处理多功能酶的问题。|https://github\.com/tttianhao/CLEAN|作为Agent数据处理的高通量计算工具，用于完成完成大规模蛋白质数据集的酶序编号填充<br>|

> 结果展示：真菌细菌SOD筛选结果展示
> 
> 

## Agent\-Env\-Interaction

### SOD酶结构特性挖掘：

1. **目标**：需要从头设计的SOD酶需要满足已经存在的SOD酶的结构与分子动力学特性。 

2. **考虑的维度**：

    1. 活性位点与静电漏斗的识别：Pymol中APBS计算分析静电特性、Lys/Arg空间分布保守性以及电荷密度计算

    2. 关键结构上的氨基酸（折叠有关）：组氨酸的残基与金属离子的配位

    3. 氨基酸带电情况：研究氨基酸的残基带电情况

    4. 主链与侧链的原子坐标：CIF文件里三维坐标

    5. 侧链二面角（氨基酸电荷取向） ： 计算主链与侧链的夹角（外接）

3. **聚类**：对Pool中所有的SOD都计算上述维度后完成聚类，这些聚类能反应实际中酶的特性情况，作为RFD3生成骨架后必须完成的强约束验证。 

4. **筛选**： 针对性选择有代表性的酶进行MD模拟得到动态结构稳定的酶 

### **AI\-ENV **

- Toolset

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OTZlZjI0ZDE4Y2VjMGUwNzk5Zjk1NTEwMTQzMjdkNzVfMTFjY2UyODg5Mzk0Y2JmZTc2MGUwMGNkYWZhZWQ5OWJfSUQ6NzYyMzU1NjkxNjAwMTcyMTUyM18xNzgxOTQxNTE4OjE3ODIwMjc5MThfVjM)

- 技术路线： **agent\+memory\+env\-\>trajectory\+report**

    - **PyMOL 沙盒 \+ AI agent 闭环**：AI结合用户指令自主完成PyMolAI 的交互，保存日志并且实时截图，在需要计算时自动读取log选择参数完成专业的计算。 

- 结果分析：见HTML

## Protein\-Gen\-Eva    

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YzkxYTVlODE0NGNmNTA5MjIyNTkyMjliOTEzMmZiNjVfMjRmOTczZGZmYzRiNGE3ZGFiNGY4YmQ2MTlhYWU3OWVfSUQ6NzYyMzU1ODY0OTY4MzY5MjczM18xNzgxOTQxNTE4OjE3ODIwMjc5MThfVjM)



流水线图中每个节点均可点击，**信息来自Agent\-env交互的trajectory，比如：**

- **RFdiffusion3** 负责在固定 His47/49/126 的 motif 约束下，生成包裹 Cu 离子的三维骨架

- **LigandMPNN** 感知 Cu 配体环境，在骨架上填充最优氨基酸序列，同时锁定三个配位残基不变

- **AlphaFold3** 以多种子、多循环方式重折叠验证，通过 pLDDT / PAE 筛选高置信度设计 

输入

```JSON
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

# 展望

1. 任务泛化后，不仅仅做一种酶的设计，而是多种蛋白质的从头设计

2. 做一个harness去更加高效的利用专业工具，数据库解决问题

3. 举例：目前AI4S较好的平台环境

https://openbio\.tech/

https://biomni\.stanford\.edu/

# 优化酶实验记录

**TL;DR** : 使用RFD去做设计SOD和界面，应该有两种思路：一种是利用C2结构对称性进行De novo 对称蛋白设计，但是这样做的坏处是与原文的事实不符合需要多次验证RMSD高于1\.0（\<1\.0是可用的）需要多次实验可用率中等；另一种是保留界面做partia RFD结果是不能同时锁定集合结构只能保证序列，但**口袋装配错误，**所以骨架可用率很低，建议如果保存天然界面直接用MPNN，用**6D52直接MPNN可用率有0\.85以上**

### Direct Interface Redesign 

天然 SOD酶（比如：E8XDJ8） 已经存在明确的蛋白\-蛋白界面而且很可能是**多层级界面**（dimer 界面 \+ tetramer 界面）。这正是 Cu,Zn\-SOD 家族的进化特征。 

静电漏斗和界面是什么关系？  

> 溶剂 \(底物 O₂⁻ 从这里来\)
> 
> ↓ ↓ ↓
> 
> ╔═════════╗
> 
> ║ 静电漏斗 ║  ← 朝外开口
> 
> ║   Cu\-Zn  ║  ← 活性位点（埋在 β\-barrel 内）
> 
> ║          ║
> 
> ║ β\-barrel ║
> 
> ║          ║
> 
> ╠═════════╣  ← 二聚体界面（朝向另一个亚基）
> 
> ╔═════════╗
> 
> ║          ║  ← 另一个亚基
> 
> ║   Cu\-Zn  ║
> 
> ║ 静电漏斗 ║
> 
> ╚═════════╝
> 
> ↓ ↓ ↓
> 
> 溶剂（另一个底物入口） 
> 
> 

### 界面设计的方式

界面在 Mn\-SOD 里是什么样的？它由 **A 链和 B 链之间**的疏水接触、盐桥、氢键网络共同构成，涉及几十个残基——这些残基**完全不在你的 motif 里**，RFD 也**完全不知道这些残基的存在**。

#### partial diffusion稳定的天然四聚体（**Direct Interface Redesign**）

**任务本质**：partial diffusion —— 保留 SodC 整体骨架，只重塑界面残基。

```Plain Text
RFdiffusion 输入：
   完整的 6D52 四聚体结构
   锁定：7 × 4 = 28 个催化残基
   锁定：每个单体的核心 β-barrel
   允许变化：界面残基的侧链 + 小幅骨架扰动
        ↓
RFdiffusion 生成：
   骨架几乎相同的四聚体
   界面残基被优化（更紧密、更稳定）
        ↓
输出：增强稳定性的 SodC 四聚体
```

- **是否需要界面**：✅ 必须有，并且界面就是设计目标

- **是否保留 SodC 骨架**：✅ 几乎完整保留

- **静电漏斗保持**：✅ 自动保持（因为活性位点周围的骨架没动）

- **难度**：低（保守 redesign）

- **适合场景**：你想做的"界面工程"教科书案例 

#### symm对称设计创造新型组装（最有创新性）

**任务本质**：把 SOD 活性位点作为 motif，让 RFdiffusion 设计一个新的二聚体/三聚体/纤维状组装。

```Plain Text
例如：把 SOD 活性位点嫁接到 CsgA 上
   ↓
RFdiffusion 输入：
   SOD 活性位点 motif (7 残基)
   + CsgA β-strand 锚定区
        ↓
输出：CsgA 框架内带有 SOD 催化功能的纤维蛋白
       —— 这就是你之前做的 CsgA-SOD fusion 的 AI 版本
```

- **是否需要界面**：✅ 需要设计**全新**界面

- **是否保留 SodC 骨架**：❌ 不保留

- **难度**：高（de novo binder/oligomer design）

- **适合场景**：你想做创新性的 enzyme functionalization  

#### 二级结构为什么会有"范围"

因为二级结构（α\-helix、β\-strand）**本来就是由多个相邻残基一起形成的**——单独一个氨基酸不能叫 helix。

- α\-helix：通常需要**至少 4 个**连续氨基酸通过氢键卷成螺旋。

- β\-strand：通常需要**至少 3 个**连续氨基酸伸展成片状。

所以当我们说"His 28 所在的 helix"时，这条 helix 是由比如 27、28、29、30、\.\.\.、40 这一连串残基**共同**形成的螺旋。

- **His 28** 本身：单数，1 个氨基酸 ✅

- **His 28 所在的 helix**：一个范围，包含 14 个氨基酸（27–40） ✅ 

因此在RFD选择：从"His 28 一个残基"扩展到"His 28 所在那一整段 helix"。 

方法：RFdiffusion Partial diffusion 

从某个中间扩散步 t 开始去噪，保留主体折叠但允许局部重构。

#### 关键参数设置

#### 
**质量检查**

align RMSD 应该 \< 1\.0 Å。如果某些设计 \> 2\.0 Å，说明 partial\_T 太大破坏了 motif，应该剔除。  

### 具体试验参数与记录

**6D52实验**

#### 情况 A：确认是天然四聚体（最可能）

✅ Direct Interface Redesign 完全可行
 ✅ 有现成的 tight dimer 界面 \+ dimer\-dimer 界面两个 redesign target
 ✅ **建议优先 redesign dimer\-dimer 界面**，因为它进化保守度低、可塑性高，改动不易破坏催化骨架



实验对象：

实验记录：

### RFD \(partial\_T=10\) vs v2 \(partial\_T=50\) 对比

v3 效果总结：

- 全局折叠保留：全局 RMSD \~2 Å，SOD 的 β\-barrel 折叠完好

- 催化位点稳定：7 个金属配位残基偏移仅 1\.8–3\.3 Å（骨架水平，侧链由 ProteinMPNN 恢复后会更精确）

- 界面微调成功：界面区域 RMSD 1\.5–3\.1 Å，有足够的结构变化来优化 packing，但没有破坏整体

- 设计多样性：design 间 pairwise RMSD \~2\.6 Å，10 个 design 结构上有差异，提供了筛选空间

---

#### bash代码：

```Markdown

# 重新验证输入：
#!/bin/bash
# run_rfdiffusion_mnsod_motif.sh

set -e

# ===== 路径配置 =====
RFDIFF_DIR=/path/to/RFdiffusion
INPUT_PDB=/path/to/inputs/6qv9_chainA_clean.pdb
OUTPUT_DIR=/path/to/output/mnsod_scaffolding_v1
mkdir -p $OUTPUT_DIR

# ===== 关键参数 =====
NUM_DESIGNS=50              # 先跑 50 个看质量，再放大
TOTAL_LEN_MIN=160           # 目标蛋白总长下限
TOTAL_LEN_MAX=220           # 总长上限

# ===== contigmap 说明 =====
# 10-30/      → N端新生成残基
# A19-45/     → 固定α1（含His27），DSSP边界21-43两端各+2缓冲
# 15-40/      → linker
# A66-89/     → 固定α2（含His81），68-87两端各+2缓冲
# 15-40/      → linker
# A153-173/   → 固定β+α3（含Asp161、His165），155-171两端各+2缓冲
# 10-30       → C端新生成残基

HYDRA_FULL_ERROR=1 python $RFDIFF_DIR/scripts/run_inference.py \
    inference.input_pdb=$INPUT_PDB \
    inference.output_prefix=$OUTPUT_DIR/design \
    inference.num_designs=$NUM_DESIGNS \
    'contigmap.contigs=[10-30/A19-45/15-40/A66-89/15-40/A153-173/10-30]' \
    "contigmap.length=${TOTAL_LEN_MIN}-${TOTAL_LEN_MAX}" \
    inference.ckpt_override_path=$RFDIFF_DIR/models/Base_ckpt.pt \
    2>&1 | tee $OUTPUT_DIR/run.log

echo "RFdiffusion done. Outputs in $OUTPUT_DIR"
ls $OUTPUT_DIR/design_*.pdb | wc -l
```

```Bash
# ===== 关键参数 =====
NUM_DESIGNS=50              # 先跑 50 个看质量，再放大
TOTAL_LEN_MIN=160           # 目标蛋白总长下限
TOTAL_LEN_MAX=220           # 总长上限


python scripts/run_inference.py \
  --config-name symmetry \
  inference.input_pdb=/mnt/shared-storage-gpfs2/yangyajie-gpfs02/RFdiffusion/input/6qv9_chainA_clean.pdb \
  inference.output_prefix=/mnt/shared-storage-gpfs2/yangyajie-gpfs02/RFdiffusion/outputs/6qv9_chainA/design_dimer_fix \
  inference.num_designs=20 \
  inference.symmetry=c2 \
  'contigmap.contigs=[20-20/A19-45/30-30/A66-89/30-30/A153-173/20-20]' \
  potentials.olig_intra_all=True \
  potentials.olig_inter_all=True \
  'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]' \
  potentials.guide_scale=2.0 \
  potentials.guide_decay=quadratic \
  inference.ckpt_override_path=/mnt/shared-storage-gpfs2/yangyajie-gpfs02/RFdiffusion/models/Base_ckpt.pt
```

#### C2分析

##### 优势：结果总览

✅ 表面上的好指标

##### 不足：

1. 几何问题很大，链间 backbone 严重碰撞

——**两条链不是"形成 dimer 界面",而是物理穿插**。119 个接触意味着 chain A 的 70% 残基都和 chain B 在化学键长度尺度上重叠,任何 MD 模拟都会爆炸,湿实验也根本无法折叠。 

2. 两个 Mn 中心距离只有 9\.35 Å 

——两个金属位点挤在一起,根本不像 SOD 二聚体的两个独立活性中心,而是"重叠在界面上"。 

#### partial\_rfd结果

```Markdown
#!/bin/bash
RFDIFF_DIR=/mnt/shared-storage-gpfs2/yangyajie-gpfs02/RFdiffusion
INPUT_PDB=$(pwd)/input/6qv9_dimer_trimmed.pdb
OUTPUT_DIR=$(pwd)/outputs/6qv9_partial_dimmer
mkdir -p $OUTPUT_DIR

CONTIG='[197-197/0 197-197]'
PROVIDE='[25-25,79-79,159-159,163-163,222-222,276-276,356-356,360-360]'

HYDRA_FULL_ERROR=1 python $RFDIFF_DIR/scripts/run_inference.py \
    inference.input_pdb=$INPUT_PDB \
    inference.output_prefix=$OUTPUT_DIR/design_partial \
    inference.num_designs=20 \
    contigmap.contigs="$CONTIG" \
    contigmap.provide_seq="$PROVIDE" \
    diffuser.partial_T=20 \
    2>&1 | tee $OUTPUT_DIR/run.log

```

**partial结果**

**1\. 全 design 只有 GLY/HIS/ASP 三种氨基酸**:

```Plain Text
residue types: ['ASP', 'GLY', 'HIS']
```

194 个非锁定残基**全部是 GLY**。这说明 RFdiffusion 这次没有运行 sequence design — 只做了 backbone 几何采样,然后填充 polyG \+ 锁定位的 HIS/ASP。**这是正常的 RFdiffusion 行为**\(它只设计骨架,序列要交给 MPNN\),但**意味着这个 pdb 不是最终设计**,只是骨架。

**2\. Mn\-Mn 距离只有 13\.31 Å**:

- 天然 6qv9 dimer:**19\.4 Å**\(你之前给我的数字\)

- 你这次设计:**13\.31 Å**\(明显偏近 \~30%\)

- partial\_T=20 是从天然结构加 40% 噪声再去噪,期望最终结构接近天然 — 但**链间几何明显偏离了天然**

**3\. Chain A 口袋几何很差**:

- HIS\-ASP 距离 15\.05 Å\(应 \~7 Å\)

- HIS\-HIS 距离 13\.65 Å\(应 \~9 Å\)

- 一对残基\(HIS CA 到中心 4\.97 Å\)还算对,但其余三个 CA 距中心 7\.7\-8\.6 Å,偏远

**4\. Chain A 和 Chain B 几何**\(理论上 C2 对称应当一致\):

- Chain B 口袋:6\.01, 6\.55, 6\.61, 7\.57 Å — 紧凑

- Chain A 口袋:4\.97, 7\.72, 7\.80, 8\.60 Å — 散开

两个口袋**不对称**,说明 partial\_T=20 的噪声让两条链各自漂走了不同的距离,没保持 C2 对称。

5. **trb 里 ****`con_ref_pdb_idx`**** 是空的**:

```Plain Text
ref chains: {}
hal chains: {}
```

这证实了我之前的判断:**这套 partial\_T 配置下,RFdiffusion 没把任何残基当 motif 处理**。所有 394 个残基都参与 SO3 扩散,只有 8 个位置通过 `provide_seq` 锁了氨基酸 — 但氨基酸序列锁定**不强约束几何位置**,这就是 Mn\-Mn 距离从 19\.4 → 13\.31 Å 的原因。 



所以partial不适合去RFD

- **链间最近骨架原子距离 0\.79 Å**\(应该 ≥ 3\.5 Å\)

- **34 对原子距离 \< 2\.0 Å**\(实际碰撞\)

- **两个 Mn 中心距离 9\.35 Å**\(真实 Mn\-SOD dimer 约 18\-25 Å\)

PyMOL 默认的可视化看 cyan/orange 配色会让两条链显得"井然有序",但实际上**它们在 3D 空间里穿插**。你用 PyMOL 命令 `find_pairs polymer.protein, polymer.protein, mode=0, cutoff=2` 之类的可以肉眼看到一堆 inter\-chain contact 在化学键长度尺度上 — 那就是 clash。所以 PyMOL 那份"design shows excellent confidence"是**只看了 pLDDT**,没看物理可行性 — 真不能拿 pLDDT 当 dimer 质量的唯一判据。

#### 总体对比：

Alphafold记录：

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NGZiOTQ0YjEzYzcyNjU2NDYyMzE0NDgyM2RjOTg1MzFfOTFlMzUzMTJiMWI4NDhkNjkyNzM4ZTU3NDk5Y2VhMTdfSUQ6NzY0NjI1NTczMDYyMjc2MTk0MF8xNzgxOTQxNTE4OjE3ODIwMjc5MThfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjU5ZTZkMWY4MDFiNWQwYjA0MGJhYzNiYTJjMjZhMmFfYmU5NTQxZGE3NjVjMTdiMjcyN2M4YzI5NjE2NjZhNzJfSUQ6NzY0NjI1NjEwMjU0MzY1ODE3N18xNzgxOTQxNTE4OjE3ODIwMjc5MThfVjM)

