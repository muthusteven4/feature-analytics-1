import argparse
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("DATABASE_URL", "sqlite:///./analytics.db")

from app.db.database import SessionLocal, init_db
from app.models.event import FeatureEvent

FEATURES = [
    "netflix_on_us",
    "satellite_connect",
    "sms_text_message",
    "voice_call",
    "mobile_hotspot",
    "syncup_tracker",
    "international_roaming",
    "wifi_calling",
    "visual_voicemail",
    "magenta_edge_upgrade",
]

FEATURE_WEIGHTS = [25, 8, 30, 20, 10, 5, 4, 10, 5, 3]
PLANS = ["magenta", "magenta_max", "essentials", "prepaid", "business"]
DEVICES = ["mobile", "tablet", "watch", "hotspot_device", "syncup_iot"]
REGIONS = ["west", "central", "east", "southeast", "northeast"]


def make_events(count):
    now = datetime.now(timezone.utc)
    events = []
    for _ in range(count):
        ts = now - timedelta(days=random.randint(0, 1825))
        feature = random.choices(FEATURES, weights=FEATURE_WEIGHTS, k=1)[0]
        user_id = f"user-{random.randint(1, 500):04d}"
        meta = {
            "plan": random.choice(PLANS),
            "device": random.choice(DEVICES),
            "region": random.choice(REGIONS),
        }
        events.append(
            FeatureEvent(
                timestamp=ts,
                user_id=user_id,
                feature=feature,
                metadata_json=json.dumps(meta),
            )
        )
    return events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()

    try:
        if args.reset:
            deleted = db.query(FeatureEvent).delete()
            db.commit()
            print(f"deleted {deleted} existing events.")

        events = make_events(args.count)
        db.bulk_save_objects(events)
        db.commit()
        print(f"seeded {len(events)} events.")
        print("visit http://localhost:8000/docs to explore.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
