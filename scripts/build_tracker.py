#!/usr/bin/env python3
"""metrics/substack_tracker.xlsx を作る（Google スプレッドシートにもそのまま取り込めます）。

  python scripts/build_tracker.py          # 既にファイルがあれば上書きしない
  python scripts/build_tracker.py --force  # 作り直す（入力済みデータは消えます）
"""
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import DataBarRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

OUT = Path(__file__).resolve().parent.parent / "metrics" / "substack_tracker.xlsx"

FONT = "Arial"
BLUE = Font(name=FONT, color="0000FF")
BLACK = Font(name=FONT)
GREEN = Font(name=FONT, color="008000")
BOLD = Font(name=FONT, bold=True)
HEAD = Font(name=FONT, bold=True, color="FFFFFF")
HEAD_FILL = PatternFill("solid", fgColor="1F4E78")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
THIN = Border(bottom=Side(style="thin", color="BFBFBF"))
ROWS = 200  # 数式を事前に入れておく行数

PCT, INT, USD, JPY = "0.0%;-0.0%;-", "#,##0;-#,##0;-", "$#,##0.00;-$#,##0.00;-", "¥#,##0;-¥#,##0;-"


def header(ws, cols, widths):
    for i, (name, w) in enumerate(zip(cols, widths), 1):
        c = ws.cell(row=1, column=i, value=name)
        c.font, c.fill = HEAD, HEAD_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 34
    ws.freeze_panes = "B2"


def build():
    wb = Workbook()

    # ------------------------------------------------------------ 使い方
    guide = wb.active
    guide.title = "使い方"
    lines = [
        ("Japan Grocery Signals 数値トラッカー", BOLD),
        ("", None),
        ("■ 入力するのは黄色いセル（青字）だけ。黒字は自動計算です。", None),
        ("■ 号ごと：公開 1 週間後に Substack の Stats（各投稿の Email 数値）を転記", None),
        ("■ 月次：毎月末に Subscribers ページのフォロワー数・購読者数を転記", None),
        ("■ 設定：価格・為替・手数料・目標を自分の数字に合わせて変更", None),
        ("■ 2 行目は記入例です。実データを入れるときに上書きしてください。", None),
        ("", None),
        ("色の意味", BOLD),
        ("青字・黄色背景 = 入力欄", None),
        ("黒字 = 計算式（触らない）", None),
        ("緑字 = 「設定」シートから参照している値", None),
        ("", None),
        ("※ 手数料は概算です。Substack 10%、Stripe 2.9%+$0.30 で計算しています。", None),
        ("   実際の手数料は Stripe のダッシュボードで確認し、「設定」シートで直してください。", None),
    ]
    for r, (text, font) in enumerate(lines, 1):
        c = guide.cell(row=r, column=1, value=text)
        c.font = font or BLACK
    guide["A1"].font = Font(name=FONT, bold=True, size=14)
    guide.column_dimensions["A"].width = 90
    for r in (10, 11, 12):
        guide.cell(row=r, column=1).font = [BLUE, BLACK, GREEN][r - 10]
    guide["A10"].fill = INPUT_FILL

    # ------------------------------------------------------------ 設定
    st = wb.create_sheet("設定")
    header(st, ["項目", "値", "メモ"], [30, 14, 60])
    settings = [
        ("月額プラン価格（USD）", 8, USD, "自分の設定価格に変更"),
        ("年額プラン価格（USD）", 80, USD, "自分の設定価格に変更"),
        ("為替レート（円/USD）", 150, "0.0", "月に一度くらい更新"),
        ("Substack 手数料率", 0.10, PCT, "Substack 公表の手数料（要確認）"),
        ("Stripe 手数料率", 0.029, PCT, "概算。国・カード種別で変わるので要確認"),
        ("Stripe 固定手数料（USD/件）", 0.30, USD, "概算。要確認"),
        ("目標：月の手取り（円）", 100000, JPY, "今回の目標"),
        ("目標：フォロワー数", 1000, INT, "今回の目標"),
    ]
    for r, (name, val, fmt, memo) in enumerate(settings, 2):
        st.cell(row=r, column=1, value=name).font = BLACK
        c = st.cell(row=r, column=2, value=val)
        c.font, c.fill, c.number_format = BLUE, INPUT_FILL, fmt
        st.cell(row=r, column=3, value=memo).font = BLACK
    # 名前の代わりに絶対参照で使うセル
    S = {k: f"設定!$B${i}" for i, k in enumerate(
        ["monthly", "yearly", "fx", "ss_fee", "stripe_pct", "stripe_fix", "goal_jpy", "goal_fol"], 2)}

    # ------------------------------------------------------------ 号ごと
    iss = wb.create_sheet("号ごと")
    cols = ["公開日", "タイトル", "URL", "送信数", "開封数", "開封率", "クリック数", "クリック率",
            "新規フリー購読", "新規有料購読", "解約", "返信数", "Notes 投稿数", "テーマの型", "メモ・学び"]
    header(iss, cols, [12, 40, 28, 10, 10, 10, 10, 10, 12, 12, 8, 8, 10, 16, 40])
    example = ["2026-11-07", "(例) What Japan's konbini put on shelves this week",
               "https://japangrocerysignals.substack.com/p/...", 120, 60, None, 9, None,
               5, 1, 0, 2, 3, "新商品", "写真多めが好評"]
    inputs = {1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 13, 14, 15}
    for r in range(2, ROWS + 2):
        for c in range(1, len(cols) + 1):
            cell = iss.cell(row=r, column=c)
            cell.border = THIN
            if c in inputs:
                cell.font, cell.fill = BLUE, INPUT_FILL
                if r == 2:
                    cell.value = example[c - 1]
        iss.cell(row=r, column=6, value=f'=IF(D{r}>0,E{r}/D{r},"")').font = BLACK
        iss.cell(row=r, column=8, value=f'=IF(E{r}>0,G{r}/E{r},"")').font = BLACK
        for c, fmt in ((4, INT), (5, INT), (6, PCT), (7, INT), (8, PCT), (9, INT), (10, INT),
                       (11, INT), (12, INT), (13, INT)):
            iss.cell(row=r, column=c).number_format = fmt
        iss.cell(row=r, column=1).number_format = "yyyy-mm-dd"
    iss["A2"].comment = Comment("2 行目は記入例。実データで上書きしてください。", "tracker")
    iss.conditional_formatting.add(f"F2:F{ROWS + 1}", DataBarRule(
        start_type="num", start_value=0, end_type="num", end_value=1, color="5B9BD5"))

    # ------------------------------------------------------------ 月次
    mo = wb.create_sheet("月次")
    cols = ["月", "フォロワー数", "無料購読者", "有料（月額）", "有料（年額）", "有料合計",
            "有料転換率", "MRR（USD）", "手数料（USD）", "手取り（USD）", "手取り（円）",
            "収入目標達成率", "フォロワー目標達成率", "前月比 フォロワー", "前月比 有料"]
    header(mo, cols, [10, 12, 12, 12, 12, 10, 11, 12, 12, 12, 13, 13, 14, 13, 11])
    example = ["2026-11", 3, 1, 0, 0]
    for r in range(2, 26):
        for c in range(1, 6):
            cell = mo.cell(row=r, column=c)
            cell.font, cell.fill, cell.border = BLUE, INPUT_FILL, THIN
            if r == 2:
                cell.value = example[c - 1]
        f = {
            6: f'=IF(A{r}="","",D{r}+E{r})',
            7: f'=IF(A{r}="","",IF(C{r}+F{r}=0,"",F{r}/(C{r}+F{r})))',
            # 年額は 12 で割って月換算
            8: f'=IF(A{r}="","",D{r}*{S["monthly"]}+E{r}*{S["yearly"]}/12)',
            # Substack 手数料 + Stripe（率 + 固定。年額の固定費は 12 で按分）
            9: f'=IF(A{r}="","",H{r}*({S["ss_fee"]}+{S["stripe_pct"]})'
               f'+(D{r}+E{r}/12)*{S["stripe_fix"]})',
            10: f'=IF(A{r}="","",H{r}-I{r})',
            11: f'=IF(A{r}="","",J{r}*{S["fx"]})',
            12: f'=IF(A{r}="","",K{r}/{S["goal_jpy"]})',
            13: f'=IF(A{r}="","",B{r}/{S["goal_fol"]})',
            14: f'=IF(OR(A{r}="",{r}=2),"",B{r}-B{r - 1})' if r > 2 else '=""',
            15: f'=IF(OR(A{r}="",{r}=2),"",F{r}-F{r - 1})' if r > 2 else '=""',
        }
        for c, formula in f.items():
            cell = mo.cell(row=r, column=c, value=formula)
            cell.font, cell.border = BLACK, THIN
        for c, fmt in ((2, INT), (3, INT), (4, INT), (5, INT), (6, INT), (7, PCT), (8, USD),
                       (9, USD), (10, USD), (11, JPY), (12, PCT), (13, PCT), (14, INT), (15, INT)):
            mo.cell(row=r, column=c).number_format = fmt
    mo["A2"].comment = Comment("2 行目は記入例（11/6 開始時点）。実データで上書きしてください。", "tracker")
    for col in ("L", "M"):
        mo.conditional_formatting.add(f"{col}2:{col}25", DataBarRule(
            start_type="num", start_value=0, end_type="num", end_value=1, color="70AD47"))

    # ------------------------------------------------------------ サマリー
    sm = wb.create_sheet("サマリー", 1)
    sm.column_dimensions["A"].width = 28
    sm.column_dimensions["B"].width = 16
    last = "LOOKUP(2,1/(月次!$A$2:$A$25<>\"\"),月次!{c}$2:{c}$25)"
    rows = [
        ("最新月", f'=IFERROR({last.format(c="$A")},"")', None),
        ("フォロワー数", f'=IFERROR({last.format(c="$B")},0)', INT),
        ("フォロワー目標", f"={S['goal_fol']}", INT),
        ("フォロワー目標達成率", "=IF(B4=0,0,B3/B4)", PCT),
        ("有料購読者", f'=IFERROR({last.format(c="$F")},0)', INT),
        ("有料転換率", f'=IFERROR({last.format(c="$G")},0)', PCT),
        ("手取り（円/月）", f'=IFERROR({last.format(c="$K")},0)', JPY),
        ("収入目標（円/月）", f"={S['goal_jpy']}", JPY),
        ("収入目標達成率", "=IF(B9=0,0,B8/B9)", PCT),
        ("目標まであと何人の有料購読者", f"=IF({S['monthly']}=0,\"\",MAX(0,ROUNDUP((B9-B8)/{S['fx']}"
                                         f"/({S['monthly']}*(1-{S['ss_fee']}-{S['stripe_pct']})"
                                         f"-{S['stripe_fix']}),0)))", INT),
        ("", None, None),
        ("号ごと平均 開封率", '=IFERROR(AVERAGE(号ごと!F2:F201),"")', PCT),
        ("号ごと平均 クリック率", '=IFERROR(AVERAGE(号ごと!H2:H201),"")', PCT),
        ("配信した号数", '=COUNTA(号ごと!B2:B201)', INT),
    ]
    sm["A1"] = "サマリー（自動計算）"
    sm["A1"].font = Font(name=FONT, bold=True, size=14)
    for r, (label, formula, fmt) in enumerate(rows, 2):
        if not label:
            continue
        sm.cell(row=r, column=1, value=label).font = BOLD
        c = sm.cell(row=r, column=2, value=formula)
        c.font = GREEN if "設定!" in formula and "LOOKUP" not in formula else BLACK
        if fmt:
            c.number_format = fmt
    sm["A12"] = "※「目標まであと何人」は月額プランだけで埋める場合の概算"
    sm["A12"].font = Font(name=FONT, italic=True, color="808080")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"created: {OUT}")


if __name__ == "__main__":
    if OUT.exists() and "--force" not in sys.argv:
        sys.exit(f"already exists: {OUT}（作り直すなら --force。入力済みデータは消えます）")
    build()
