from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw_anchor_records.json"
GENERATED_PATH = ROOT / "data" / "generated_anchor_candidates.json"
RULE_VERSION = "anchor-rules-v0.1"


EXCLUDE_PATTERNS = [
    ("포함 여부", "검증 조건은 독립 앵커가 아니라 상위 경험의 확인 항목으로 내려갑니다."),
    ("불포함", "불포함/주의 문구는 긍정 앵커로 쓰지 않습니다."),
    ("버스", "MVP 도시 내 이동에서는 버스 앵커를 제외합니다."),
    ("호텔", "숙소는 경험 앵커가 아니라 accommodation_candidates/MCP 숙소 후보로 분리합니다."),
    ("숙소", "숙소는 경험 앵커가 아니라 accommodation_candidates/MCP 숙소 후보로 분리합니다."),
]

FOOD_KEYWORDS = ["야타이", "라멘", "타코야키", "오코노미야키", "쿠시카츠", "시장", "먹거리", "해산물"]
TRANSIT_KEYWORDS = ["역", "공항", "항", "터미널"]
PLACE_KEYWORDS = ["스튜디오", "타워", "성", "공원", "마을", "거리", "수족관", "가이유칸", "도톤보리", "광안리"]
SALES_WORDS = ["입장권", "패스", "투어", "티켓", "예약", "단독", "특가", "옵션"]


def slugify(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z가-힣]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "anchor"


def strip_sales_words(name: str) -> str:
    result = name
    for word in SALES_WORDS:
        result = result.replace(word, "")
    result = re.sub(r"\s+", " ", result).strip(" ·-/")
    return result or name


def classify(record: dict) -> tuple[str, str]:
    text = f"{record['name']} {record.get('description', '')}"
    if any(keyword in text for keyword in FOOD_KEYWORDS):
        return "뭐 먹지", "FOOD"
    if any(keyword in text for keyword in TRANSIT_KEYWORDS):
        return "도시 내 이동", "TRANSIT"
    if any(keyword in text for keyword in PLACE_KEYWORDS):
        return "뭐 하지", "PLACE"
    return "뭐 하지", "PLACE"


def decide_status(record: dict, confidence: float) -> tuple[str, str]:
    text = f"{record['name']} {record.get('description', '')}"
    for pattern, reason in EXCLUDE_PATTERNS:
        if pattern in text:
            return "REJECTED", reason
    if confidence >= 0.78:
        return "AUTO_ACCEPT", "공식성·반복 신호·상품 신호가 충분해 자동 후보로 채택합니다."
    return "NEEDS_REVIEW", "근거는 있으나 자동 노출 전 사람이 검수해야 합니다."


def score(record: dict) -> float:
    official = 0.35 if record.get("official") else 0.0
    product = min(int(record.get("product_count", 0)), 8) / 8 * 0.25
    repeats = min(int(record.get("repeat_count", 0)), 12) / 12 * 0.30
    named = 0.10 if len(strip_sales_words(record["name"])) >= 2 else 0.0
    return round(official + product + repeats + named, 2)


def generate() -> dict:
    records = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    candidates = []
    run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    for record in records:
        normalized_name = strip_sales_words(record["name"])
        category, anchor_type = classify(record)
        confidence = score(record)
        status, reason = decide_status(record, confidence)
        candidates.append(
            {
                "id": f"candidate-{record['city_id']}-{slugify(normalized_name)}",
                "run_id": run_id,
                "city_id": record["city_id"],
                "source_type": record["source_type"],
                "source_record_id": record["source_record_id"],
                "raw_name": record["name"],
                "normalized_name": normalized_name,
                "category": category,
                "anchor_type": anchor_type,
                "confidence": confidence,
                "automation_status": status,
                "reason": reason,
                "product_signal": int(record.get("product_count", 0)),
                "official_signal": 1 if record.get("official") else 0,
                "repeats_signal": int(record.get("repeat_count", 0)),
            }
        )

    summary = {
        "run_id": run_id,
        "rule_version": RULE_VERSION,
        "source_snapshot_path": str(RAW_PATH.relative_to(ROOT)),
        "generated_path": str(GENERATED_PATH.relative_to(ROOT)),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(records),
        "accepted_candidates": sum(1 for item in candidates if item["automation_status"] == "AUTO_ACCEPT"),
        "review_candidates": sum(1 for item in candidates if item["automation_status"] == "NEEDS_REVIEW"),
        "rejected_candidates": sum(1 for item in candidates if item["automation_status"] == "REJECTED"),
    }
    payload = {"summary": summary, "candidates": candidates}
    GENERATED_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    payload = generate()
    summary = payload["summary"]
    print(
        "generated "
        f"{summary['total_records']} raw records -> "
        f"{summary['accepted_candidates']} accepted, "
        f"{summary['review_candidates']} review, "
        f"{summary['rejected_candidates']} rejected"
    )
    print(f"exported {GENERATED_PATH}")


if __name__ == "__main__":
    main()
