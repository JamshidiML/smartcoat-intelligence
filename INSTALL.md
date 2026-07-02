# Install SmartCoat Release 1.4 — Implementation Scaffold

This release introduces the first implementation scaffold for the SmartCoat Knowledge Capture MVP.

It adds source code, tests, database migrations, Docker Compose, `.env.example`, and implementation architecture notes.

Because this release may add or update root-level files such as `pyproject.toml` and `docker-compose.yml`, review the diff before committing.

Use `rsync` to merge safely.

From the root of your existing repository:

```bash
cd ~/smartcoat/smartcoat-intelligence

rm -rf /tmp/smartcoat_release_1_4
mkdir -p /tmp/smartcoat_release_1_4
unzip ~/Downloads/smartcoat_release_1_4_implementation_scaffold.zip -d /tmp/smartcoat_release_1_4

rsync -av /tmp/smartcoat_release_1_4/ ./

git status
git diff --stat
git add -A
git commit -m "Add Implementation Scaffold release 1.4"
git push origin main
```

After installation, create or update your conda environment:

```bash
conda activate smartcoat
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run the API locally:

```bash
uvicorn smartcoat.api.main:app --reload
```
