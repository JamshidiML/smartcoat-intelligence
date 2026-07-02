# Install SmartCoat Release 1.5 — Database & Persistence Layer

Use `rsync` to merge safely.

```bash
cd ~/smartcoat/smartcoat-intelligence

rm -rf /tmp/smartcoat_release_1_5
mkdir -p /tmp/smartcoat_release_1_5
unzip ~/Downloads/smartcoat_release_1_5_database_persistence_layer.zip -d /tmp/smartcoat_release_1_5

rsync -av /tmp/smartcoat_release_1_5/ ./

git status
git diff --stat
git add -A
git commit -m "Add Database Persistence Layer release 1.5"
git push origin main
```

After installation:

```bash
conda activate smartcoat
pip install -e ".[dev]"
pytest
```

Optional local database:

```bash
docker compose up -d postgres
python scripts/init_db.py
uvicorn smartcoat.api.main:app --reload
```
