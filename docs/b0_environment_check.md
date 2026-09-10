# B0 环境与数据证据验收

> 执行日期：2026-09-08  
> 阶段：B0  
> 结论：通过

## 1. 执行范围

B0 只完成项目结构、独立环境、数据来源/完整性和非结果字段检查。未运行按 `segment` 分组的 `visit`、`conversion` 或 `spend` 效果分析，未进入 B1。

## 2. 独立环境

- 环境位置：`.venv/`
- Python：3.12.7
- pandas：3.0.5
- numpy：2.5.3
- scipy：1.18.0
- statsmodels：0.15.0
- matplotlib：3.11.1
- seaborn：0.13.2
- pytest：9.1.1

自检结果：

- [x] 七个指定直接依赖全部导入成功。
- [x] NumPy `dot` 浮点计算正常。
- [x] Matplotlib `Agg` 后端生成临时 PNG 成功。
- [x] 临时测试图已删除，未混入项目交付。

## 3. 输入完整性

- 输入：`data/raw/hillstrom.csv`
- 大小：3,964,977 字节
- 行数：64,000
- 列数：12
- SHA-256：`0E5893329D8B93CEFECC571777672028290AB69865718020C78C7284F291AECE`

列名：

```text
recency,history_segment,history,mens,womens,zip_code,newbie,channel,segment,visit,conversion,spend
```

## 4. 非结果字段检查

- `recency`：整数，范围 1–12。
- `history`：浮点数，范围 29.99–3,345.93。
- `history_segment`：7 个预期消费区间。
- `mens`、`womens`、`newbie`：仅取 0/1。
- `zip_code`：`Rural`、`Surburban`、`Urban`。`Surburban` 是源文件拼写，原始数据未改。
- `channel`：`Multichannel`、`Phone`、`Web`。
- `segment`：`Mens E-Mail`、`No E-Mail`、`Womens E-Mail`。
- 上述非结果字段缺失总数：0。
- 数据无客户 ID，无法在 B0 独立证明每行必然是唯一客户；未使用整行去重。

## 5. B0 Gate

- [x] 项目独立目录结构已建立。
- [x] Git 仓库已初始化。
- [x] 独立 Python 环境已建立。
- [x] 指定依赖导入、数值和绘图自检通过。
- [x] 数据来源、大小、行列数和 SHA-256 已记录。
- [x] 原始 CSV 只作读取输入，未手工修改。
- [x] `.venv/` 和 `data/raw/hillstrom.csv` 被 Git 忽略。
- [x] 未生成任何组间效果比较。

## 6. 下一阶段边界

B1 开始前不运行组间结果分析。B1 需要先创建并冻结 `docs/analysis_plan.md`，记录文件哈希和修订日志，然后才能进入 B2/B3。
