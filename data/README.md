# Hillstrom 原始数据记录

## 文件

- 本地文件：`raw/hillstrom.csv`
- 下载日期：2026-09-08
- 文件大小：3,964,977 字节
- 数据行数（不含表头）：64,000
- 列数：12
- SHA-256：`0E5893329D8B93CEFECC571777672028290AB69865718020C78C7284F291AECE`

## 来源

- 原始发布说明：<https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html>
- 发布方 CSV：<http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv>
- 下载方式：从发布方 HTTP 直链下载。
- 说明：HTTPS 直链在 2026-09-08 因远程站点证书名称/证书链错误而失败；未绕过 TLS 验证，改用发布方仍可访问的 HTTP 直链。

## 结构验证

列名：

```text
recency,history_segment,history,mens,womens,zip_code,newbie,channel,segment,visit,conversion,spend
```

实验组行数：

| segment | rows |
|---|---:|
| Mens E-Mail | 21,307 |
| No E-Mail | 21,306 |
| Womens E-Mail | 21,387 |
| 合计 | 64,000 |

## 使用规则

1. `raw/hillstrom.csv` 作为只读原始证据，不手工修改。
2. 原始数据中 `Surburban` 为源文件自带拼写；如需改为 `Suburban`，只能在处理脚本和 `data/processed/` 中进行并记录映射。
3. 分析前重新计算 SHA-256；不一致时停止并查明原因。
4. 原始 CSV 不提交 Git；仓库只保留本文档中的下载与校验信息。

## 干净克隆后的数据准备

在仓库根目录运行：

```powershell
.\scripts\prepare_data.ps1
```

脚本只在`data/raw/hillstrom.csv`不存在时下载。写入项目目录前会依次校验文件大小、SHA-256、表头和64,000行；任一检查失败都会停止。若目标位置已经存在正确文件，脚本只复核哈希，不重复下载；若已有文件哈希错误，脚本不会覆盖，需要先人工审计文件来源。

发布方下载地址仅提供HTTP，因此固定SHA-256是不可跳过的完整性门禁。脚本不绕过TLS，也不接受哈希不同的镜像文件。

## PowerShell 校验命令

```powershell
Get-FileHash -LiteralPath '.\data\raw\hillstrom.csv' -Algorithm SHA256
(Import-Csv -LiteralPath '.\data\raw\hillstrom.csv').Count
```
