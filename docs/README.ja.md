# ResearchStat AI

科学研究のための AI ネイティブ統計解析・再現性プラットフォーム。

デフォルトのプロジェクト紹介は簡体字中国語です。正式な中国語版はルート
[README.md](../README.md) にあります。

[English](README.en.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

V1 は次の閉じたワークフローを実装しています。

```text
AI プランニング
  -> Protocol バインド
  -> 人間によるレビュー
  -> Python/R エンジン
  -> クロスエンジン検証
  -> Audit Trail
  -> 出版品質の Figure
```

## 主な機能

- Protocol Registry: YAML で手法・仮定・posthoc・alpha・欠損値方針・効果量を定義。
- AI Planner: 自然言語を構造化プランに変換し、Registry 内の Protocol のみを選択。
- Human Review: 推奨 Protocol を承認または上書きし、理由を記録。
- Multi Engine: 同じリクエストを Python/R で実行し、交差検証。
- Validation: NIST StRD・R 公式データセット・境界データを使用。
- Audit Trail: 分析ごとに `analysis_record.json` を生成。
- Figure Engine: 編集可能な SVG・PDF・300 DPI TIFF、scatter/boxplot/violin/survival をサポート。
- Privacy: 列のマスキング、識別子ハッシュ、一時ディレクトリ自動削除。
- MCP: stdio・SSE・streamable-http の 3 トランスポート。

## インストール

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[figure,test,mcp]"
```

## クイックスタート

コードを読みたくない場合は、[チュートリアル](TUTORIAL.md)（簡体字中国語）を
先に読んでください。Agent にそのままコピーできるプロンプトがあります。

サンプルデータ: `examples/data/tutorial_data.csv`

```python
import pandas as pd
from researchstat.workflow import run_analysis_workflow

data = pd.read_csv("examples/data/tutorial_data.csv")

output = run_analysis_workflow(
    user_input="compare three drugs on mouse tumor size",
    data=data,
    outcome="value",
    group="group",
    audit_dir="audit",
)
print(output["result"].model_dump())
```

## MCP

```powershell
.\.venv\Scripts\python.exe -m researchstat.mcp.cli --transport stdio
.\.venv\Scripts\python.exe -m researchstat.mcp.cli --transport streamable-http --port 8000
```

公開ツール:

- `list_protocols`
- `plan_analysis`
- `execute_analysis`
- `render_figure`

## テスト

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe benchmarks\run_performance.py
```

## ドキュメント

- プロジェクト計画: `PROJECT_PLAN.md`
- チュートリアル: `docs/TUTORIAL.md`
- 競合調査: `docs/RESEARCH_LESSONS.md`
- オープンソースエコシステム: `docs/ECOSYSTEM.md`
- V1 受け入れ: `docs/V1_ACCEPTANCE.md`
- 論文原稿: `docs/PAPER.md`
- 初心者向けチュートリアル: `docs/TUTORIAL.md`

## ライセンス

MIT。詳細は `LICENSE`、サードパーティライセンスは `NOTICE` を参照。
