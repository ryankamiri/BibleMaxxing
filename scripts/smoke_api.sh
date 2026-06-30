#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
BASE_URL="${BASE_URL%/}"

if [[ "$BASE_URL" == */biblemaxxing ]]; then
  SERVICE_BASE="$BASE_URL"
else
  SERVICE_BASE="$BASE_URL/biblemaxxing"
fi

API_BASE="$SERVICE_BASE/api/v1"
RUN_ID="$(date +%s)"
PRIMARY_EMAIL="smoke+${RUN_ID}@example.com"
SECONDARY_EMAIL="smoke-commenter+${RUN_ID}@example.com"

json_field() {
  python3 -c '
import json
import sys

path = sys.argv[1].split(".")
value = json.load(sys.stdin)
for part in path:
    if part.isdigit():
        value = value[int(part)]
    else:
        value = value[part]
print(value)
' "$1"
}

first_video_id() {
  python3 -c '
import json
import sys

payload = json.load(sys.stdin)
for item in payload.get("items", []):
    if item.get("type") == "video" and item.get("video"):
        print(item["video"]["id"])
        raise SystemExit(0)
raise SystemExit("No video item returned")
'
}

first_creator_id() {
  python3 -c '
import json
import sys

payload = json.load(sys.stdin)
for item in payload.get("items", []):
    video = item.get("video")
    creator = video.get("creator") if video else None
    if creator and creator.get("id"):
        print(creator["id"])
        raise SystemExit(0)
raise SystemExit("No creator returned")
'
}

post_json() {
  local url="$1"
  local body="$2"
  local token="${3:-}"
  if [[ -n "$token" ]]; then
    curl -fsS -X POST "$url" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      -d "$body"
  else
    curl -fsS -X POST "$url" \
      -H "Content-Type: application/json" \
      -d "$body"
  fi
}

patch_json() {
  local url="$1"
  local body="$2"
  local token="$3"
  curl -fsS -X PATCH "$url" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "$body"
}

get_auth() {
  local url="$1"
  local token="$2"
  curl -fsS "$url" -H "Authorization: Bearer $token"
}

echo "Checking $SERVICE_BASE/health"
curl -fsS "$SERVICE_BASE/health" >/dev/null

primary="$(post_json "$API_BASE/auth/register" "{\"username\":\"smoke${RUN_ID}\",\"email\":\"${PRIMARY_EMAIL}\",\"password\":\"password123\",\"birthday\":\"2005-01-01\"}")"
token="$(printf '%s' "$primary" | json_field access_token)"

secondary="$(post_json "$API_BASE/auth/register" "{\"username\":\"smokecommenter${RUN_ID}\",\"email\":\"${SECONDARY_EMAIL}\",\"password\":\"password123\",\"birthday\":\"2005-01-01\"}")"
secondary_token="$(printf '%s' "$secondary" | json_field access_token)"
secondary_id="$(printf '%s' "$secondary" | json_field user.id)"

post_json "$API_BASE/onboarding" '{"topicSlugs":["Prayer","Workplace holiness","Bible study"],"intensity":"balanced"}' "$token" >/dev/null

if ingest_body="$(post_json "$API_BASE/admin/ingest/sample" '{}' "${ADMIN_TOKEN:-$token}" 2>/tmp/biblemaxxing-smoke-ingest.err)"; then
  echo "Sample ingest: $ingest_body"
else
  echo "Sample ingest skipped or unavailable: $(cat /tmp/biblemaxxing-smoke-ingest.err)"
fi

feed="$(get_auth "$API_BASE/feed?limit=8" "$token")"
video_id="$(printf '%s' "$feed" | first_video_id)"
creator_id="$(printf '%s' "$feed" | first_creator_id)"

post_json "$API_BASE/feed/impressions" "{\"videoID\":\"${video_id}\",\"position\":0}" "$token" >/dev/null
post_json "$API_BASE/videos/${video_id}/watch" '{"secondsWatched":610,"percentComplete":1,"rewatched":true,"eventType":"complete"}' "$token" >/dev/null
post_json "$API_BASE/videos/${video_id}/like" '{}' "$token" >/dev/null
post_json "$API_BASE/videos/${video_id}/save" '{}' "$token" >/dev/null
post_json "$API_BASE/videos/${video_id}/not-interested" '{"reason":"smoke check"}' "$token" >/dev/null

comment="$(post_json "$API_BASE/videos/${video_id}/comments" '{"body":"Smoke check comment."}' "$token")"
comment_id="$(printf '%s' "$comment" | json_field id)"
post_json "$API_BASE/videos/${video_id}/comments" '{"body":"Secondary smoke comment."}' "$secondary_token" >/dev/null
get_auth "$API_BASE/videos/${video_id}/comments" "$token" >/dev/null

post_json "$API_BASE/comments/${comment_id}/report" '{"reason":"smoke report","details":"API smoke check"}' "$token" >/dev/null
post_json "$API_BASE/videos/${video_id}/report" '{"reason":"smoke video report","details":"API smoke check"}' "$token" >/dev/null
post_json "$API_BASE/users/${secondary_id}/block" '{}' "$token" >/dev/null
post_json "$API_BASE/creators/${creator_id}/block" '{}' "$token" >/dev/null
get_auth "$API_BASE/search?q=prayer" "$token" >/dev/null
get_auth "$API_BASE/reflection/next" "$token" >/dev/null

if get_auth "$API_BASE/admin/reports" "${ADMIN_TOKEN:-$token}" >/dev/null 2>/tmp/biblemaxxing-smoke-admin.err; then
  patch_json "$API_BASE/admin/comments/${comment_id}/moderation" '{"status":"hidden","notes":"smoke check"}' "${ADMIN_TOKEN:-$token}" >/dev/null
  get_auth "$API_BASE/admin/audit-log" "${ADMIN_TOKEN:-$token}" >/dev/null
else
  echo "Admin checks skipped or unavailable: $(cat /tmp/biblemaxxing-smoke-admin.err)"
fi

curl -fsS -X DELETE "$API_BASE/me" -H "Authorization: Bearer $secondary_token" >/dev/null
curl -fsS -X DELETE "$API_BASE/me" -H "Authorization: Bearer $token" >/dev/null

echo "BibleMaxxing API smoke passed for $SERVICE_BASE"
