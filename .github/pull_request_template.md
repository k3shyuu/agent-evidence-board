## Summary

## Evidence / Safety Impact

- [ ] This change does not add secrets, cookies, private chat exports, or production credentials.
- [ ] New examples are synthetic or explicitly public-safe.
- [ ] New gate behavior has negative tests.
- [ ] Documentation was updated when behavior changed.

## Checks

```bash
python -m compileall src tests
python -m unittest discover -s tests
```
