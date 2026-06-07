# Contributing

Contributions should improve evidence quality, safety, or maintainability.

Useful contributions:

- new validators for common hallucination/failure modes;
- better public-source capture with clear boundaries;
- tests for false positives and false negatives;
- schemas for reviews, judge decisions, and publication records;
- documentation for agent workflows.

Before opening a pull request:

```bash
python -m compileall src tests
python -m unittest discover -s tests
```

Do not commit secrets, `.env` files, cookies, private exports, generated databases, or production logs.
