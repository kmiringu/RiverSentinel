"""Shared data loaders for the RiverSentinel app — precomputed exports only, no Earth Engine."""
import csv
import json
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
PROCESSED_DIR = REPO_ROOT / 'data' / 'processed'

CANDIDATE_NUMERIC_FIELDS = [
    'lon', 'lat', 'riverside_pct', 'rest_pct', 'diff_pp',
    'wide_riverside_pct', 'wide_rest_pct', 'wide_diff_pp', 'best_diff_pp',
]


def load_summary():
    with open(PROCESSED_DIR / 'pipeline_summary.json') as f:
        return json.load(f)


def load_candidates():
    with open(PROCESSED_DIR / 'combined_riparian_hotspots.csv') as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for key in CANDIDATE_NUMERIC_FIELDS:
            row[key] = float(row[key])
    return rows


def image_path(name):
    return str(PROCESSED_DIR / name)
