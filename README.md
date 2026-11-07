# Substack 80%自動化キット（Japan Grocery Signals）

海外向け note＆メルマガ（Substack）を「ほぼ自動」で回すための、プロンプト・ルール・テンプレート置き場です。
対象：<https://substack.com/@japangrocerysignals>

目標
- まずはフォロワー 1,000 人
- 有料転換率の改善
- 月 10 万円の継続収入（ほぼ自動運用）

## 役割分担

| 担当 | 役割 |
| --- | --- |
| ChatGPT（メイン） | 企画出し・テーマ候補・英語全文の作成 |
| Claude（添削係） | ネイティブ視点の添削、トーン・事実関係チェック |
| 自分 | 選ぶ・一次情報を渡す・最終承認する |

## 運用フロー（毎週）

`（ ）` が自分の作業。それ以外は AI に任せます。

| STEP | 作業 | 自分の作業 | 使うファイル |
| --- | --- | --- | --- |
| 1 | テーマ候補 5 案を生成 | （候補を見る） | `prompts/02_theme_candidates.md` |
| 2 | 1 案を選ぶ | （番号で選択） | — |
| 3 | 写真・一次情報を収集 | （写真や音声メモを渡す） | `prompts/03_primary_info_intake.md` |
| 4 | 01〜05 の英語全文作成 | （原稿を確認） | `prompts/04_newsletter_draft.md` |
| 5 | 経験・意見の反映＋Claude 添削 | （修正希望を伝える） | `prompts/05_claude_review.md` |
| 6 | Substack に下書き入稿 | （プレビューを確認） | `prompts/06_publish_checklist.md` |
| 7 | 画像・ペイウォールを配置して公開 | （最終承認） | `prompts/06_publish_checklist.md` |

初回だけ：`prompts/01_niche_research.md` でニッチ選定 → Substack 登録 → Stripe 接続 → プロフィール整備。

## 「往復ゼロ」にするコツ：ルールの蓄積

ChatGPT ⇄ Claude の往復で出てきた指摘は、毎回 **`rules/style_rules.md` に 1 行で追記** します。
次回からはこのファイルをプロンプトと一緒に渡すだけで、確認は 1 回で済むようになります。

## 号ごとの作業フォルダ

```bash
./scripts/new_issue.sh "theme-slug"
# => issues/2026-11-07_theme-slug/ が作られ、テンプレートがコピーされます
```

各フォルダには `issue.md`（テーマ・一次情報・原稿・添削ログ・公開チェック）が入ります。
過去号がたまるほど、テーマの重複チェックや「よく伸びた型」の分析に使えます。

## ファイル構成

```
prompts/
  01_niche_research.md      # 初回のみ：勝てるニッチの抽出
  02_theme_candidates.md    # STEP1：テーマ候補5案
  03_primary_info_intake.md # STEP3：写真・音声メモから一次情報を整理
  04_newsletter_draft.md    # STEP4：01〜05の英語全文
  05_claude_review.md       # STEP5：Claude添削
  06_publish_checklist.md   # STEP6-7：入稿・公開チェック
rules/
  style_rules.md            # 往復で生まれたルール（随時追記）
  publication_profile.md    # ニュースレターの基本設定（毎回AIに渡す）
templates/
  issue.md                  # 号ごとの作業テンプレート
scripts/
  new_issue.sh              # 号フォルダの作成
issues/                     # 各号の作業ログ
```

## 注意点
- Substack には公式の投稿 API がないため、STEP6 の入稿は「AI が整えた原稿をコピペ」が現実的な最短ルートです。
- AI の出力は事実関係（価格・統計・社名・日付）を必ず自分で確認してから公開してください。
- 写真は自分で撮影したもの、または使用許諾のあるものだけを使います。
