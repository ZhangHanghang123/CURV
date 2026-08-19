import requests
import json
import sys

BASE = "http://43.143.253.186"
PREFIX = "/curv/api"
# 1. login
r = requests.post(f"{BASE}{PREFIX}/auth/login", data={"username": "admin", "password": "admin123"})
token = r.json()["data"]["token"]
print(f"token ok: {token[:20]}...")
# 2. collect
r = requests.post(
    f"{BASE}{PREFIX}/collection/run",
    headers={"Authorization": f"Bearer {token}"},
    json={"start_date": "2025-08-18", "end_date": "2026-08-17"},
    timeout=600,
)
data = r.json()["data"]
print(f"总记录: {data['total_records']}")
print(f"耗时: {data['duration_ms']} ms")
print(f"曲线数: {len(data['curves'])}")
for c in data["curves"]:
    print(f"  {c['code']:30s} -> {c['count']} 行")