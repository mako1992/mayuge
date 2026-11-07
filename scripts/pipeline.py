#!/usr/bin/env python3
"""Substack 週次パイプライン：STEP1〜5 をまとめて実行する。

プロンプト本文は prompts/*.md のコードブロックをそのまま使う（Markdown が唯一の正）。
各 STEP の出力は issues/<日付>_<slug>/ に保存されるので、途中から再開できる。

使い方:
  python scripts/pipeline.py run                       # STEP1 から通しで実行
  python scripts/pipeline.py run --issue issues/2026-11-07_xxx --from 4   # STEP4 から再開
  python scripts/pipeline.py run --dry-run             # API を呼ばず、組み立てたプロンプトを保存
                                                       # （ChatGPT に貼って使う場合もこれ）
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
RULES = ROOT / "rules"
ISSUES = ROOT / "issues"
TEMPLATE = ROOT / "templates" / "issue.md"

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
IMAGE_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
               ".webp": "image/webp", ".gif": "image/gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGES = 20

# 各 STEP の出力ファイル
F_THEMES, F_SELECTED, F_NOTES = "01_themes.md", "02_selected.md", "notes.md"
F_INTAKE, F_DRAFT, F_COMMENTS = "03_intake.md", "04_draft.md", "comments.md"
F_FINAL = "05_final.md"


# ---------------------------------------------------------------- helpers
def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def prompt_block(name: str) -> str:
    """prompts/<name> の最初の ``` コードブロックを返す。"""
    m = re.search(r"```\n(.*?)```", read(PROMPTS / name), re.S)
    if not m:
        sys.exit(f"コードブロックが見つかりません: prompts/{name}")
    return m.group(1).strip()


def fill(template: str, values: dict[str, str]) -> str:
    for key, val in values.items():
        template = template.replace(key, val)
    return template


def system_prompt() -> str:
    return (
        "The following files are attached to every request.\n\n"
        f"<publication_profile>\n{read(RULES / 'publication_profile.md')}\n</publication_profile>\n\n"
        f"<style_rules>\n{read(RULES / 'style_rules.md')}\n</style_rules>"
    )


def past_titles() -> str:
    titles = []
    for f in sorted(ISSUES.glob("*/02_selected.md")):
        first = read(f).strip().splitlines()
        if first:
            titles.append(f"- {first[0].lstrip('# ').strip()}")
    return "\n".join(titles) or "(none yet)"


def ask(msg: str) -> str:
    try:
        return input(msg)
    except EOFError:
        return ""


def confirm(msg: str) -> bool:
    return ask(f"{msg} [y/N]: ").strip().lower() in {"y", "yes"}


def load_images(photo_dir: Path) -> list[dict]:
    blocks = []
    for p in sorted(photo_dir.iterdir()) if photo_dir.exists() else []:
        mt = IMAGE_TYPES.get(p.suffix.lower())
        if not mt:
            if p.suffix.lower() in {".heic", ".heif"}:
                print(f"  ! {p.name}: HEIC は非対応です。JPEG に変換してください")
            continue
        if p.stat().st_size > MAX_IMAGE_BYTES:
            print(f"  ! {p.name}: 5MB を超えているのでスキップ（縮小してください）")
            continue
        if len(blocks) >= MAX_IMAGES:
            print(f"  ! 画像は最大 {MAX_IMAGES} 枚までです。残りはスキップ")
            break
        blocks.append({"type": "text", "text": f"[Photo file: {p.name}]"})
        blocks.append({"type": "image", "source": {
            "type": "base64", "media_type": mt,
            "data": base64.standard_b64encode(p.read_bytes()).decode()}})
    return blocks


# ---------------------------------------------------------------- Claude
class Runner:
    def __init__(self, dry_run: bool):
        self.dry_run = dry_run
        self.client = None
        if not dry_run:
            try:
                import anthropic
            except ImportError:
                sys.exit("anthropic が未インストールです: pip install -r requirements.txt")
            self.anthropic = anthropic
            self.client = anthropic.Anthropic()

    def call(self, out: Path, text: str, effort: str, images: list[dict] | None = None) -> str:
        """Claude を呼び、結果を out に保存して返す。dry-run ならプロンプトを保存。"""
        if self.dry_run:
            prompt_file = out.with_name(out.stem + ".prompt.md")
            note = f"\n\n(+ {len(images) // 2} photos)" if images else ""
            prompt_file.write_text(f"{system_prompt()}\n\n---\n\n{text}{note}\n", encoding="utf-8")
            print(f"  [dry-run] プロンプトを保存: {prompt_file.relative_to(ROOT)}")
            print(f"  → ChatGPT 等の回答を {out.relative_to(ROOT)} に保存してから次へ進んでください")
            if not out.exists():
                out.write_text("", encoding="utf-8")
            ask("  保存したら Enter: ")
            return read(out)

        content = (images or []) + [{"type": "text", "text": text}]
        print(f"  Claude ({MODEL}, effort={effort}) で生成中…", flush=True)
        try:
            with self.client.beta.messages.stream(
                model=MODEL,
                max_tokens=64000,
                system=system_prompt(),
                output_config={"effort": effort},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                messages=[{"role": "user", "content": content}],
            ) as stream:
                msg = stream.get_final_message()
        except self.anthropic.AuthenticationError:
            sys.exit("API キーが無効です。ANTHROPIC_API_KEY を確認してください")
        except self.anthropic.RateLimitError:
            sys.exit("レート制限に達しました。少し待ってから --from で再開してください")
        except self.anthropic.APIStatusError as e:
            sys.exit(f"API エラー ({e.status_code}): {e.message}")
        except self.anthropic.APIConnectionError:
            sys.exit("ネットワークエラー。接続を確認して --from で再開してください")

        if msg.stop_reason == "refusal":
            sys.exit("Claude が回答を辞退しました。素材や指示を見直してください")
        result = "".join(b.text for b in msg.content if b.type == "text").strip()
        if msg.stop_reason == "max_tokens":
            print("  ! 出力が上限で切れました。内容を確認してください")
        out.write_text(result + "\n", encoding="utf-8")
        print(f"  保存: {out.relative_to(ROOT)}  (in {msg.usage.input_tokens} / out {msg.usage.output_tokens} tokens)")
        return result


# ---------------------------------------------------------------- steps
def create_issue_dir(slug: str) -> Path:
    date = dt.date.today().isoformat()
    slug = re.sub(r"[^a-z0-9-]", "", slug.lower().replace(" ", "-")) or "issue"
    d = ISSUES / f"{date}_{slug}"
    n = 2
    while d.exists():
        d, n = ISSUES / f"{date}_{slug}-{n}", n + 1
    (d / "photos").mkdir(parents=True)
    (d / "issue.md").write_text(
        read(TEMPLATE).replace("{{SLUG}}", slug).replace("{{DATE}}", date), encoding="utf-8")
    return d


def step1_2(r: Runner, staging: Path) -> Path:
    print("\n=== STEP 1: テーマ候補 5 案 ===")
    staging.mkdir(parents=True, exist_ok=True)
    text = fill(prompt_block("02_theme_candidates.md"), {
        "[past titles]": "\n" + past_titles(),
        "[optional]": ask("今週の時事ネタ・季節イベントがあれば（なければ Enter）: ").strip() or "none",
    })
    themes = r.call(staging / F_THEMES, text, effort="medium")
    print("\n" + themes + "\n")

    print("=== STEP 2: 1 案を選ぶ ===")
    while True:
        num = ask("番号を選んでください (1-5): ").strip()
        if num in {"1", "2", "3", "4", "5"}:
            break
    chosen = extract_candidate(themes, int(num))
    slug = ask("フォルダ名に使う英語スラッグ（例: konbini-winter-sweets）: ").strip()
    d = create_issue_dir(slug)
    (staging / F_THEMES).rename(d / F_THEMES)
    for p in staging.glob("*.prompt.md"):
        p.rename(d / p.name)
    if not any(staging.iterdir()):
        staging.rmdir()
    (d / F_SELECTED).write_text(chosen + "\n", encoding="utf-8")
    print(f"  作成: {d.relative_to(ROOT)}")
    return d


def extract_candidate(themes: str, num: int) -> str:
    """出力から num 番の候補ブロックを切り出す（失敗したら全文＋番号を返す）。"""
    pattern = rf"(?ms)^\s*(?:#+\s*)?\**\s*(?:Candidate\s*)?{num}[.)]\s.*?(?=^\s*(?:#+\s*)?\**\s*(?:Candidate\s*)?{num + 1}[.)]\s|\Z)"
    m = re.search(pattern, themes)
    if m:
        return m.group(0).strip()
    return f"# Candidate {num}\n\n(Selected number {num} from the list below)\n\n{themes}"


def step3(r: Runner, d: Path) -> None:
    print("\n=== STEP 3: 写真・一次情報 ===")
    notes = d / F_NOTES
    if not notes.exists():
        notes.write_text("<!-- 音声メモの文字起こし・メモ書きを日本語でそのまま貼ってください -->\n",
                         encoding="utf-8")
    print(f"  写真 → {(d / 'photos').relative_to(ROOT)}/  （JPEG/PNG/WebP、1枚5MBまで）")
    print(f"  メモ → {notes.relative_to(ROOT)}")
    ask("  入れ終わったら Enter: ")
    images = load_images(d / "photos")
    print(f"  写真 {len(images) // 2} 枚を読み込みました")
    text = fill(prompt_block("03_primary_info_intake.md"), {
        "[選んだ案をそのまま貼る]": read(d / F_SELECTED).strip(),
    }) + f"\n\n<my_notes>\n{read(notes).strip()}\n</my_notes>"
    print("\n" + r.call(d / F_INTAKE, text, effort="medium", images=images) + "\n")
    if confirm("足りない素材を追加して STEP3 をやり直しますか？"):
        step3(r, d)


def step4(r: Runner, d: Path) -> None:
    print("\n=== STEP 4: 01〜05 英語全文 ===")
    text = fill(prompt_block("04_newsletter_draft.md"), {
        "[selected topic]": read(d / F_SELECTED).strip(),
        "[STEP3 output]": "\n" + read(d / F_INTAKE).strip(),
    })
    r.call(d / F_DRAFT, text, effort="high")
    print(f"  原稿を確認してください: {(d / F_DRAFT).relative_to(ROOT)}")


def step5(r: Runner, d: Path) -> None:
    print("\n=== STEP 5: 経験・意見の反映＋Claude 添削 ===")
    comments = d / F_COMMENTS
    if not comments.exists():
        comments.write_text("<!-- 原稿への修正希望・自分の経験や意見を日本語で書いてください -->\n",
                            encoding="utf-8")
    print(f"  修正希望 → {comments.relative_to(ROOT)}")
    ask("  書き終わったら Enter: ")
    text = fill(prompt_block("05_claude_review.md"), {
        "[自分のコメント]": "\n" + read(comments).strip(),
    }) + f"\n\n<draft>\n{read(d / F_DRAFT).strip()}\n</draft>"
    result = r.call(d / F_FINAL, text, effort="high")
    append_new_rules(result)
    print(f"\n完了！最終稿: {(d / F_FINAL).relative_to(ROOT)}")
    print("次は prompts/06_publish_checklist.md に沿って Substack に入稿してください。")


def append_new_rules(review: str) -> None:
    m = re.search(r"(?is)NEW RULES.*?\n(.*?)(?=\n#+\s|\n[A-Z]\.\s|\Z)", review)
    rules = [re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip()
             for line in (m.group(1).splitlines() if m else [])
             if re.match(r"^\s*(?:[-*]|\d+[.)])\s+\S", line)]
    if not rules:
        print("  （NEW RULES は見つかりませんでした）")
        return
    print("\n  Claude が提案した新ルール:")
    for rule in rules:
        print(f"   - {rule}")
    if confirm("  rules/style_rules.md に追記しますか？"):
        today = dt.date.today().isoformat()
        with open(RULES / "style_rules.md", "a", encoding="utf-8") as f:
            for rule in rules:
                f.write(f"- {today}: {rule}\n")
        print("  追記しました")


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description="Substack 週次パイプライン（STEP1〜5）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="STEP1〜5 を順に実行")
    run.add_argument("--issue", type=Path, help="再開する号フォルダ（--from 3 以降で必須）")
    run.add_argument("--from", dest="start", type=int, default=1, choices=[1, 3, 4, 5],
                     help="開始 STEP（1=テーマ出し, 3=一次情報, 4=原稿, 5=添削）")
    run.add_argument("--dry-run", action="store_true",
                     help="API を呼ばずにプロンプトだけ保存（ChatGPT に貼る用）")
    args = ap.parse_args()

    r = Runner(args.dry_run)
    if args.start == 1:
        d = step1_2(r, ISSUES / "_staging")
    else:
        if not args.issue or not args.issue.is_dir():
            sys.exit("--from 3 以降は --issue <号フォルダ> を指定してください")
        d = args.issue.resolve()

    steps = {3: step3, 4: step4, 5: step5}
    for n in (3, 4, 5):
        if n >= max(args.start, 3):
            steps[n](r, d)


if __name__ == "__main__":
    main()
