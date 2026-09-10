# 实施偏差与补全记录

## 2026-09-10：B1冻结协议与初始B4实现对齐

### 审计发现

在编写B0–B6详细学习手册时，逐项对照`docs/analysis_plan.md`和实际输出，发现初始B4/B6漏生成两项已经在B1冻结的分析：

1. 使用全样本合并Spend P99.5作为统一上限的缩尾敏感性分析；
2. 毛利率20%/40%/60% × 每名客户邮件成本$0.01/$0.05/$0.10的固定经济场景网格。

初始实现以收入区间下界说明决策阈值，但不能替代冻结协议中的完整3×3场景表。此前“B4/B6完全通过”的表述因此过宽。

### 处理

- 在`src/analyze_b4.py`中按冻结规则新增`winsorized_spend_effects`和`economic_scenarios`。
- 主入口新增`winsorized_spend_effects.csv`和`economic_scenarios.csv`，纳入B6输出哈希。
- 新增统一阈值、不修改原始数据、场景数量和公式测试。
- 更新B4报告、总报告、README和详细学习手册。

### 结果与边界

- P99.5统一阈值为$68.37135；缩尾后P1/P2仍为正且Holm校正后通过。
- 18个经济场景显示部分低毛利/高成本组合不支持正贡献，不能把增量收入直接等同利润。
- 本次没有更换主指标、排除原始记录或替换B3主结果。
- 两项规则在查看组间结果前已经写入冻结协议；本次属于迟延实现已冻结规则，不是根据结果新增方法。迟延实施本身仍在此记录中披露。

### 文件名映射

B1协议列出的概念性输出名与最终实现采用了更具体的文件名：

| B1概念名称 | 最终文件 |
|---|---|
| `robustness_checks.csv` | `adjusted_effects.csv`、`winsorized_spend_effects.csv` |
| `segment_effects.csv` | `subgroup_spend_effects.csv`、`interaction_tests.csv` |
| `economic_scenarios.csv` | `economic_scenarios.csv` |

文件名拆分不改变估计量，但为了审计可读性，不回写或覆盖冻结协议原文。
