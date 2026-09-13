from __future__ import annotations

from matplotlib import font_manager, rcParams
import seaborn as sns


GROUP_LABELS = {
    "No E-Mail": "不发邮件",
    "Mens E-Mail": "男装邮件",
    "Womens E-Mail": "女装邮件",
}


def set_chinese_plot_style(*, context: str = "talk") -> str:
    """Set a reproducible plotting theme and choose an installed CJK font."""
    preferred = [
        "Microsoft YaHei",
        "SimHei",
        "PingFang SC",
        "Hiragino Sans GB",
        "Noto Sans CJK SC",
        "Noto Sans CJK JP",
        "WenQuanYi Micro Hei",
        "WenQuanYi Zen Hei",
        "Arial Unicode MS",
    ]
    installed = {font.name for font in font_manager.fontManager.ttflist}
    selected = next((font for font in preferred if font in installed), "DejaVu Sans")
    sns.set_theme(style="whitegrid", context=context)
    rcParams["font.sans-serif"] = [selected, "DejaVu Sans"]
    rcParams["axes.unicode_minus"] = False
    return selected
