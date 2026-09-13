# Hillstrom 邮件营销随机实验分析

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Reproducibility checks](https://github.com/Eleven11-w/hillstrom-email-experiment-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/Eleven11-w/hillstrom-email-experiment-analysis/actions/workflows/ci.yml)

基于64,000名客户的三组公开历史随机实验，评估男装邮件、女装邮件相对不发邮件的两周客均增量销售额。项目覆盖数据完整性、ITT估计、Bootstrap置信区间、多重比较、稳健性检查、探索性异质性与业务情景，并提供从原始数据准备到结果验收的完整复现入口。

> **诚信边界**：这是公开历史实验的再分析，不是本人设计或上线的实验，也不声称真实预注册或盲态分析。`Spend`是销售收入，不是利润；没有真实成本与毛利数据时不报告ROI。

## 一分钟结论

| 对比 | 两周客均Spend增量 | Bootstrap 95% CI | Holm校正p值 | 结论 |
|---|---:|---:|---:|---|
| 男装邮件 − 不发邮件 | +$0.770 | [$0.487, $1.057] | 2.33e-7 | 正向统计证据 |
| 女装邮件 − 不发邮件 | +$0.424 | [$0.171, $0.682] | 0.00113 | 正向统计证据 |

- 男装邮件：访问率增加7.66个百分点，转化率增加0.681个百分点。
- 女装邮件：访问率增加4.52个百分点，转化率增加0.311个百分点。
- 转化率绝对MDE约0.223个百分点（双侧`alpha=0.05`、`power=0.80`）。
- 男装邮件点估计更高，但男装与女装的直接比较不足以确认“最终赢家”。
- 8项客户分层交互经Holm校正后均未通过，当前没有已验证的定向规则。

业务含义：两种邮件都值得进入新的商业验证。真实投放前仍需补充毛利、发送成本、退货、退订/投诉和长期客户价值。

## 核心图表

### 访问与转化

![三组访问率与转化率](results/figures/01_visit_conversion_rates.png)

### 客均增量销售额

![两个主要Spend效应](results/figures/02_primary_spend_effects.png)

### 零值与长尾分布

![Spend零值与正值长尾](results/figures/03_spend_distribution.png)

补充图表：[协变量调整对比](results/figures/04_adjusted_vs_unadjusted.png) · [探索性子组效应](results/figures/05_subgroup_spend_effects.png)

## 从干净克隆开始复现

基准环境为Windows PowerShell与Python 3.12。原始CSV不进入Git；准备脚本从数据发布方下载文件，并在写入项目目录前强制校验文件大小、64,000行、schema与SHA-256。发布方只提供HTTP直链，因此哈希不一致时脚本会立即停止。

```powershell
git clone https://github.com/Eleven11-w/hillstrom-email-experiment-analysis.git
Set-Location hillstrom-email-experiment-analysis

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\scripts\prepare_data.ps1

.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m src.run_all
.\.venv\Scripts\python.exe -m src.verify_release
```

预期验收信息：

```text
18 passed
B2 validation passed
B3-B5 analyses reproduced
B6 manifest completed
Generated outputs: 17
Release verification passed
```

`src.run_all`会先校验输入哈希、schema、逻辑规则、SRM和实验前平衡，再生成分析结果。不要绕过主入口挑选脚本运行。

## 数据与冻结基线

- 原始发布说明：<https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html>
- 发布方CSV：<http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv>
- 本地输入：`data/raw/hillstrom.csv`，64,000行、12列
- SHA-256：`0E5893329D8B93CEFECC571777672028290AB69865718020C78C7284F291AECE`
- 实验组：不发邮件21,306；男装邮件21,307；女装邮件21,387
- 冻结协议SHA-256：`43A7B844B3A0EC01DC0108D1B19ECC6A52FB9CA2992E9D9994C25474E82A90B8`

项目不重新分发原始CSV。数据来源、下载边界与字段说明见[`data/README.md`](data/README.md)。

## 分析设计

- **主要估计量**：所有随机分配客户的两周平均Spend差，即ITT；未访问和未购买客户的0仍进入分析。
- **主要推断**：10,000次客户级Bootstrap边际95% CI、双侧Welch检验、P1/P2的Holm校正。
- **辅助指标**：Visit和Conversion的百分点差、区间和两比例检验。
- **稳健性**：实验前协变量OLS/LPM + HC3；全样本统一P99.5缩尾敏感性。
- **业务情景**：毛利率20%/40%/60% × 邮件成本$0.01/$0.05/$0.10，仅为假设情景。
- **探索性分层**：处理×实验前特征交互；同一数据发现的模式只用于设计新实验。

完整统计口径见[冻结再分析协议](docs/analysis_plan.md)，逐步学习与复现说明见[B0–B6详细手册](docs/Hillstrom_B0-B6_详细分析与学习手册.md)。

## 项目结构

```text
hillstrom-email-experiment-analysis/
├─ data/
│  ├─ README.md                 # 来源、哈希与字段证据
│  └─ raw/                      # 本地原始数据，Git忽略
├─ docs/                        # 协议、阶段报告、总报告与面试材料
├─ results/
│  ├─ tables/                   # 12个可复现CSV
│  ├─ figures/                  # 5张中文图表
│  └─ b6_run_manifest.json      # 输入、代码、环境和输出哈希
├─ scripts/prepare_data.ps1     # 下载并验证冻结输入
├─ src/
│  ├─ validate_data.py          # B2数据门禁
│  ├─ analyze_experiment.py     # B3主分析
│  ├─ analyze_b4.py             # B4稳健性与经济情景
│  ├─ analyze_b5.py             # B5探索性分层
│  ├─ run_all.py                # B6唯一分析入口
│  └─ verify_release.py         # 发布证据核对
└─ tests/                       # 18项自动化测试
```

## 输出索引

| 内容 | 文件 |
|---|---|
| 数据QC、SRM、平衡 | `data_qc.csv`、`srm_check.csv`、`balance_check.csv` |
| 描述统计与主要结果 | `group_summary.csv`、`experiment_effects.csv` |
| MDE、精度、协变量调整 | `conversion_mde.csv`、`spend_precision.csv`、`adjusted_effects.csv` |
| 极端值敏感性与经济假设 | `winsorized_spend_effects.csv`、`economic_scenarios.csv` |
| 探索性分层与交互 | `subgroup_spend_effects.csv`、`interaction_tests.csv` |
| 最终运行证据 | [`results/b6_run_manifest.json`](results/b6_run_manifest.json) |
| 最终分析报告 | [`docs/final_report.md`](docs/final_report.md) |

## 关键限制

- 数据没有客户ID，无法独立证明每行必然是唯一客户。
- 随机分配依据发布方说明，当前CSV不能重建原始分流过程。
- 2008年历史实验的具体效果量不能直接外推到今天。
- Spend是收入而不是利润，经济场景不能替代真实成本与毛利。
- 探索性交互没有通过多重校正，不能据此部署客户定向规则。
- 图表使用系统中文字体；分析数值和CSV不受字体环境影响。

## 项目状态与简历材料

- B0–B6分析、报告与本地复现：完成。
- Gate B-Data / B-Stats / B-Business / B-Repro：通过。
- B7书面材料：完成。
- Gate B-Resume：有条件通过，待本人完成一次不超过5分钟的计时讲解。
- 当前验证：18/18项测试通过，17个生成输出与B6清单一致。

简历内容见[两条候选bullet](docs/resume_bullets.md)，五分钟讲解和12个追问答案见[面试材料](docs/interview_kit.md)，最终个人动作见[B7验收报告](docs/b7_acceptance_report.md)。
