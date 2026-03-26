#!/usr/bin/env bash
python - <<'PY'
from core.db import init_db
init_db()
print("DB initialisée")
PY
