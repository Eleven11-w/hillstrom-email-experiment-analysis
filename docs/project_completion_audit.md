# 项目完成与公开交付审计

> 审计日期：2026-09-13<br>
> 远程仓库：<https://github.com/Eleven11-w/hillstrom-email-experiment-analysis><br>
> 干净克隆验证基线：`34523ce`<br>
> 结论：分析与公开复现通过；Gate B-Resume仍待本人完成五分钟计时讲解

## 1. 阶段状态

| 阶段 | 状态 | 主要证据 |
|---|---|---|
| B0 环境与数据证据 | 通过 | `docs/b0_environment_check.md`、`data/README.md` |
| B1 冻结再分析协议 | 通过 | `docs/analysis_plan.md`、`results/run_manifest.json` |
| B2 数据质量与实验完整性 | 通过 | `docs/b2_data_quality_report.md`、三张QC表 |
| B3 描述统计与主分析 | 通过 | `docs/b3_results_summary.md`、`experiment_effects.csv` |
| B4 精度与稳健性 | 通过 | `docs/b4_robustness_report.md`、五张稳健性表 |
| B5 探索性客户分层 | 通过 | `docs/b5_subgroup_report.md`、交互检验表 |
| B6 报告与复现 | 通过 | `docs/final_report.md`、`results/b6_run_manifest.json` |
| B7 书面材料 | 通过 | `docs/resume_bullets.md`、`docs/interview_kit.md` |
| B7 本人口头验收 | 待完成 | `docs/b7_acceptance_report.md`最后一项 |

## 2. 干净克隆验证

验证没有复用原项目的原始数据或虚拟环境。执行过程为：

1. 从GitHub重新克隆远程`main`；
2. 运行`scripts/prepare_data.ps1`，从发布方HTTP直链下载CSV；
3. 在写入项目前校验3,964,977字节、64,000行、冻结表头和SHA-256；
4. 新建独立`.venv`并安装`requirements.txt`；
5. 运行18项测试；
6. 运行`python -m src.run_all`重建12个CSV和5张PNG；
7. 运行`python -m src.verify_release`核对输入、协议、代码、输出哈希和表行数。

最终结果：

```text
SHA-256 verified: 0E5893329D8B93CEFECC571777672028290AB69865718020C78C7284F291AECE
18 passed
B2 validation passed
B3-B5 analyses reproduced
B6 manifest completed
Generated outputs: 17
Release verification passed
```

首次克隆曾因Windows自动将冻结协议从LF转换为CRLF而触发协议哈希停止门禁。项目随后新增`.gitattributes`固定文本文件为LF，再次从远程全新克隆后，协议哈希恢复为冻结值且全流程通过。该失败没有被绕过；修复的是版本控制换行规则，不是放宽哈希验证。

## 3. 两类运行清单

| 文件 | 用途 |
|---|---|
| `results/run_manifest.json` | B1冻结时的输入、协议和环境证据；当时尚未运行组间效果分析 |
| `results/b6_run_manifest.json` | B6执行时的输入、协议、代码、环境、随机种子和17个输出哈希 |

两个文件不是重复产物，也不能相互覆盖。

## 4. 当前门禁结论

- Gate B-Data：通过。
- Gate B-Stats：通过。
- Gate B-Business：通过。
- Gate B-Repro：本地与GitHub干净克隆均通过。
- Gate B-Resume：书面部分通过；本人完成一次不超过5分钟且无需逐字照读的计时讲解后，才可标记完全通过。

原始数据不进入Git，项目不声称拥有或重新授权数据。分析代码、结果和文档已经公开交付，但历史实验效果不能直接外推到当前业务。
