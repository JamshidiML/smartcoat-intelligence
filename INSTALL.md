# Install SmartCoat Release 1.5.2 — Mapper Datetime Hotfix

This hotfix fixes mapper tests where SQLAlchemy records created in memory do not yet have database-generated `created_at` and `updated_at` values.

Use `rsync` to merge safely.

```bash
cd ~/smartcoat/smartcoat-intelligence

rm -rf /tmp/smartcoat_release_1_5_2
mkdir -p /tmp/smartcoat_release_1_5_2
unzip ~/Downloads/smartcoat_release_1_5_2_mapper_datetime_hotfix.zip -d /tmp/smartcoat_release_1_5_2

rsync -av /tmp/smartcoat_release_1_5_2/ ./

git status
git diff --stat
pytest
```

If tests pass:

```bash
git add -A
git commit -m "Fix mapper datetime fallback"
git push origin main
```
