# Install SmartCoat Release 1.2 — Root Repository Documentation

This release updates root-level repository documentation.

It may overwrite root files such as `README.md`, `ROADMAP.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, and `SECURITY.md`.

Use `rsync` to merge safely, then review the Git diff before committing.

From the root of your existing repository:

```bash
cd ~/smartcoat/smartcoat-intelligence

rm -rf /tmp/smartcoat_release_1_2
mkdir -p /tmp/smartcoat_release_1_2
unzip ~/Downloads/smartcoat_release_1_2_root_repository_documentation.zip -d /tmp/smartcoat_release_1_2

rsync -av /tmp/smartcoat_release_1_2/ ./

git status
git diff --stat
git add -A
git commit -m "Add Root Repository Documentation release 1.2"
git push origin main
```

If you want to review files before applying:

```bash
find /tmp/smartcoat_release_1_2 -maxdepth 3 -type f | sort
```
