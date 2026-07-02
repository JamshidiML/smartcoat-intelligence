# Install SmartCoat Release 1.6 — Persistent API Layer

This release connects the FastAPI routes to the database persistence layer through repositories.

Use `rsync` to merge safely.

```bash
cd ~/smartcoat/smartcoat-intelligence

rm -rf /tmp/smartcoat_release_1_6
mkdir -p /tmp/smartcoat_release_1_6
unzip ~/Downloads/smartcoat_release_1_6_persistent_api_layer.zip -d /tmp/smartcoat_release_1_6

rsync -av /tmp/smartcoat_release_1_6/ ./

git status
git diff --stat
pytest
```

If tests pass:

```bash
git add -A
git commit -m "Add Persistent API Layer release 1.6"
git push origin main
```

Optional database/API test:

```bash
docker compose up -d postgres
python scripts/init_db.py
uvicorn smartcoat.api.main:app --reload
```
