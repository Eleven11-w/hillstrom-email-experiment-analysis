# 电商邮件营销增量实验与客户分层分析

以下两条是正式简历候选版本；复制到简历时只保留这两条，不追加未经验证的收益或上线描述。

- 基于 Hillstrom 公开的 6.4 万名客户三组随机邮件历史数据，冻结再分析协议并搭建 Python 一键复现流程，完成数据逻辑、SRM（p=0.904）、实验前平衡和转化率 MDE 检查。
- 以两周客均 Spend 为主要指标，采用 10,000 次客户级 Bootstrap、Welch 检验和 Holm 校正，估计 Mens/Womens 邮件相对空白组分别增加 $0.770（95% CI：$0.487–$1.057）和 $0.424/客户（$0.171–$0.682），并通过 HC3 调整与交互检验区分总体效果和待复验分层线索。

## 数字证据映射

| 简历信息 | 原始证据 | 生成代码 |
|---|---|---|
| 64,000名客户、三组样本数 | `results/tables/data_qc.csv`、`srm_check.csv` | `src/validate_data.py` |
| SRM p=0.904、实验前平衡 | `srm_check.csv`、`balance_check.csv` | `src/validate_data.py` |
| 转化率MDE | `results/tables/conversion_mde.csv` | `src/analyze_b4.py` |
| Mens/Womens Spend效应和区间 | `results/tables/experiment_effects.csv` 的 P1/P2 Spend 行 | `src/analyze_experiment.py` |
| HC3稳健性 | `results/tables/adjusted_effects.csv` | `src/analyze_b4.py` |
| 分层线索未确认 | `results/tables/interaction_tests.csv` | `src/analyze_b5.py` |
| 全量复现证据 | `results/b6_run_manifest.json` | `src/run_all.py` |

## 声明边界

- 可以说“公开历史随机实验再分析”“估计增量Spend”“构建可复现流程”。
- 不说“本人独立上线实验”“真实预注册或盲态分析”“利润提升”“识别出最佳客户名单”。
- `Mens E-Mail` 和 `Womens E-Mail` 指邮件推荐品类，不代表客户性别。
