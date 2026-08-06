# Contributing

Thanks for contributing to ResearchStat AI.

## Development Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[figure,test,mcp]"
```

## Validation

Before opening a pull request, run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe benchmarks\run_performance.py
```

## Commit Messages

Use concise, conventional commit messages, for example:

```text
Add protocol search by method
Fix two-way ANOVA Type III contrast coding
Update multilingual README
```

## License

By contributing, you agree that your contributions are licensed under the MIT
License.
