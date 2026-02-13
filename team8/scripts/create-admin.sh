#!/usr/bin/env bash
set -euo pipefail
# Usage: ./scripts/create-admin.sh <email> <password> [first_name] [last_name]

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <email> <password> [first_name] [last_name]" >&2
  exit 1
fi

EMAIL="$1"
PASSWORD="$2"
FIRST_NAME="${3:-}"
LAST_NAME="${4:-}"

# Run inside the core container to create/update a superuser (uses stdin; no tricky quoting)
docker compose exec -T \
  -e EMAIL="$EMAIL" \
  -e PASSWORD="$PASSWORD" \
  -e FIRST_NAME="$FIRST_NAME" \
  -e LAST_NAME="$LAST_NAME" \
  core python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()

email = os.environ["EMAIL"]
first = os.environ.get("FIRST_NAME", "")
last = os.environ.get("LAST_NAME", "")
pw = os.environ["PASSWORD"]

user, created = User.objects.get_or_create(
    email=email,
    defaults={
        "first_name": first,
        "last_name": last,
        "is_staff": True,
        "is_superuser": True,
        "is_active": True,
    },
)
if not created:
    user.first_name = first
    user.last_name = last

user.is_staff = True
user.is_superuser = True
user.is_active = True
user.set_password(pw)
if hasattr(user, "token_version"):
    user.token_version = 0
user.save()

print("created" if created else "updated", email)
PY
