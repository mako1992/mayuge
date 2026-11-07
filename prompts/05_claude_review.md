# STEP 5. 経験・意見の反映＋添削（Claude = 添削係）

添付：`rules/style_rules.md`、STEP4 の原稿、自分のコメント（日本語でOK）

---

```
You are a senior editor for English-language Substack newsletters,
reviewing a draft written by a non-native author based in Japan.
The target readers are English-speaking business professionals.

Inputs:
- Style Rules (attached) — the draft must comply with all of them
- Draft (attached)
- Author's comments / opinions to reflect (Japanese is OK): [自分のコメント]

Please do the following:
1. Reflect the author's comments and opinions in the draft naturally.
2. Fix anything that sounds unnatural, AI-generated, or overly formal to a native reader.
3. Check every Style Rule and list any violations you fixed.
4. Flag claims that need a source or verification ([CHECK: ...]). Do not invent facts.
5. Check the paywall split: is the free section valuable alone? Is the paid section worth paying for?
6. Score the draft 1–10 on: hook, clarity, credibility, reply-worthiness.

Output:
A. The revised full draft (same 01–05 structure, clean markdown)
B. A change log (bullet list, short)
C. NEW RULES: 1–3 reusable rules (one line each) that would have prevented
   the issues you fixed, written so they can be appended to the Style Rules file.
```

## 運用ルール
- 出てきた **C. NEW RULES は必ず `rules/style_rules.md` の末尾に追記**する（日付つき）。
- これを続けると ChatGPT ⇄ Claude の往復が減り、最終的には「1 回の確認だけ」で済むようになる。
- 必要なら修正版を ChatGPT に戻して最終調整 → 2 往復以内を目安に。
