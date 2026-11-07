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

## まとめて実行（STEP1〜5）

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...      # Claude API キー
python scripts/pipeline.py run
```

1 コマンドで STEP1〜5 を順に進めます。自分の出番（番号選び・写真/メモ投入・修正希望）では止まって待ちます。

| STEP | スクリプトがやること | 自分の出番 |
| --- | --- | --- |
| 1 | テーマ候補 5 案を生成（過去号タイトルと重複しないよう自動で渡す） | 時事ネタがあれば入力 |
| 2 | 選んだ案で号フォルダ `issues/<日付>_<slug>/` を作成 | 番号とスラッグを入力 |
| 3 | `photos/` の画像と `notes.md` を読んで一次情報を整理 | 写真とメモを入れて Enter |
| 4 | 01〜05 の英語全文を作成 → `04_draft.md` | 原稿を確認 |
| 5 | `comments.md` を反映して添削 → `05_final.md`。NEW RULES を `rules/style_rules.md` に追記（確認あり） | 修正希望を書いて Enter |

- 途中から再開：`python scripts/pipeline.py run --issue issues/2026-11-07_xxx --from 4`
- **ChatGPT で書きたいとき**：`--dry-run` を付けると API を呼ばず、各 STEP のプロンプトを `*.prompt.md` に保存します。ChatGPT に貼って、回答を指定のファイルに保存すれば次の STEP に進めます（例：STEP4 だけ ChatGPT、STEP5 は Claude で `--from 5`）。
- モデルは `claude-opus-5-5`（環境変数 `CLAUDE_MODEL` で変更可）。プロンプト本文は `prompts/*.md` のコードブロックをそのまま読むので、プロンプトを直せばスクリプトにも反映されます。
- 写真は JPEG/PNG/WebP、1 枚 5MB・最大 20 枚まで。iPhone の HEIC は JPEG に変換してください。

## 数値トラッカー（シート）

`metrics/substack_tracker.xlsx`（Excel でも Google スプレッドシートでも開けます）

| シート | 中身 |
| --- | --- |
| サマリー | 最新のフォロワー数・有料転換率・手取り、目標（1,000 人／月 10 万円）の達成率、**目標まであと何人の有料購読者が必要か** |
| 号ごと | 公開 1 週間後に送信数・開封数・クリック数・新規購読・返信数を転記 → 開封率・クリック率は自動計算 |
| 月次 | 月末にフォロワー数・無料/有料購読者数を転記 → 転換率・MRR・手数料差引後の手取り（円）を自動計算 |
| 設定 | 価格・為替・手数料率・目標値（ここを変えると全シートに反映） |

入力するのは黄色いセルだけです。手数料（Substack 10%、Stripe 2.9%+$0.30）は概算なので、実際の数字に直してください。
シートを作り直すときは `python scripts/build_tracker.py --force`（入力済みデータは消えます）。

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
  pipeline.py               # STEP1〜5 をまとめて実行
  build_tracker.py          # 数値トラッカーの生成
  new_issue.sh              # 号フォルダの作成（手動運用用）
metrics/
  substack_tracker.xlsx     # 数値トラッカー
issues/                     # 各号の作業ログ
```

## 注意点
- Substack には公式の投稿 API がないため、STEP6 の入稿は「AI が整えた原稿をコピペ」が現実的な最短ルートです。
- AI の出力は事実関係（価格・統計・社名・日付）を必ず自分で確認してから公開してください。
- 写真は自分で撮影したもの、または使用許諾のあるものだけを使います。
