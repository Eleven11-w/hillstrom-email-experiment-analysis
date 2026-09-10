# B2 数据质量与实验完整性报告

状态：通过（2026-09-08）

## 输入与结构

- 输入文件：`data/raw/hillstrom.csv`
- SHA-256：`0E5893329D8B93CEFECC571777672028290AB69865718020C78C7284F291AECE`
- 规模：64,000 行、12 列；字段、类型、三组标签及二元结果取值均通过校验。
- 逻辑冲突：`conversion=0 & spend>0`、`conversion=1 & spend=0`、`conversion=1 & visit=0` 均为 0。

## 随机化完整性门禁

- 三组样本量：No E-Mail 21,306；Mens E-Mail 21,307；Womens E-Mail 21,387。
- SRM：卡方统计量 0.2025，p=0.9037，未触发停止规则。
- 连续变量最大绝对标准化差异（SMD）：0.0076。
- 分类变量最大绝对比例差：0.0084。
- 需人工复核的平衡性标记：0。

## 结论

B2 全部门禁通过，可以进入 B3。这里的平衡性结果用于诊断随机化实现，不作为“证明随机化成功”的显著性筛选。

机器可读证据位于 `results/tables/data_qc.csv`、`srm_check.csv` 和 `balance_check.csv`。
