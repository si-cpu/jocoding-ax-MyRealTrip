#!/usr/bin/env python3
"""Render a compact first-pass T&A Supply Gap Map PDF."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"
PDF_PATH = OUT / "ta_supply_gap_first_pass.pdf"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def register_font() -> str:
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
        return "HYSMyeongJo-Medium"
    except Exception:
        pass
    return "Helvetica"


def short(text: str, limit: int = 82) -> str:
    text = str(text or "").replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


class PdfWriter:
    def __init__(self, path: Path, font_name: str):
        self.c = canvas.Canvas(str(path), pagesize=A4)
        self.width, self.height = A4
        self.font_name = font_name
        self.x = 44
        self.y = self.height - 48
        self.page = 1

    def footer(self) -> None:
        self.c.setFont(self.font_name, 8)
        self.c.setFillColorRGB(0.42, 0.45, 0.50)
        self.c.drawString(44, 28, "T&A Supply Gap Map - First-pass result")
        self.c.drawRightString(self.width - 44, 28, str(self.page))

    def new_page(self) -> None:
        self.footer()
        self.c.showPage()
        self.page += 1
        self.y = self.height - 48

    def ensure(self, needed: int = 40) -> None:
        if self.y < 52 + needed:
            self.new_page()

    def text(self, value: str, size: int = 10, gap: int = 16, color=(0.12, 0.16, 0.23)) -> None:
        self.ensure(gap + 4)
        self.c.setFont(self.font_name, size)
        self.c.setFillColorRGB(*color)
        self.c.drawString(self.x, self.y, value)
        self.y -= gap

    def title(self, value: str) -> None:
        self.text(value, size=22, gap=30, color=(0.05, 0.07, 0.10))

    def h1(self, value: str) -> None:
        self.y -= 8
        self.text(value, size=15, gap=22, color=(0.05, 0.07, 0.10))

    def bullet(self, value: str) -> None:
        self.text("• " + value, size=10, gap=16)

    def save(self) -> None:
        self.footer()
        self.c.save()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    font_name = register_font()

    analysis = ROOT / "data" / "supply_gap_analysis"
    matches = read_csv(analysis / "official_mcp_anchor_matches.csv")
    scores = read_csv(analysis / "supply_gap_scores.csv")
    exact_rows = read_csv(analysis / "exports" / "supply_gap_exact_list.csv")
    detail_path = analysis / "detail_evidence" / "tour_detail_evidence.csv"
    detail_rows = read_csv(detail_path) if detail_path.exists() else []
    anchors = read_csv(ROOT / "data" / "official_tourism_sources" / "anchors" / "official_experience_anchors.csv")
    mcp_rows = read_csv(ROOT / "data" / "mcp_tna_products" / "processed" / "mcp_tna_products.csv")

    partial = [r for r in scores if r["classification"] == "부분 상품화 자산"]
    gap = [r for r in scores if r["classification"] == "상품화 부족 자산"]
    exact_partial = [r for r in exact_rows if r["classification"] == "부분 상품화 자산"]
    exact_gap = [r for r in exact_rows if r["classification"] == "상품화 부족 자산"]
    detail_counts: dict[str, int] = {}
    for row in detail_rows:
        detail_counts[row["detail_evidence_level"]] = detail_counts.get(row["detail_evidence_level"], 0) + 1

    pdf = PdfWriter(PDF_PATH, font_name)
    pdf.title("T&A Supply Gap Map")
    pdf.text("1차 결과 리포트 - 공식 관광자산 대비 마이리얼트립 상품화 연결 상태", 11, 20)
    pdf.text(f"생성일: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M')}", 9, 18, (0.42, 0.45, 0.50))

    pdf.h1("핵심 지표")
    pdf.bullet(f"공식 원천 앵커: {len(anchors)}개")
    pdf.bullet(f"1차 관광지 분석 대상(food/yatai 제외): {len(scores)}개")
    pdf.bullet(f"식음/야타이 후보: {len(anchors) - len(scores)}개")
    pdf.bullet(f"MCP 상품 샘플: {len(mcp_rows)}개")
    pdf.bullet(f"직접 제목 매칭: {len(matches)}개")
    pdf.bullet(f"투어 상세 확정(detail_confirmed): {detail_counts.get('detail_confirmed', 0)}개")
    pdf.bullet(f"부분 상품화 자산: {len(partial)}개")
    pdf.bullet(f"상품화 부족 자산: {len(gap)}개")

    pdf.h1("현재 결론")
    pdf.bullet("현재 결과는 수요 없음이 아니라, 공식 관광자산과 MCP 상품 샘플 사이의 직접 연결 표현이 약하다는 뜻이다.")
    pdf.bullet("분석 단위는 판매 방식이 아니라 장소/관광지 앵커다.")
    pdf.bullet("투어 상품은 제목 매칭만으로 방문 확정하지 않고, 상세 일정/포함사항의 긍정 근거가 필요하다.")
    pdf.bullet("불포함 사항에만 등장한 장소는 긍정 근거로 사용하지 않는다.")

    pdf.h1("직접 매칭된 공식 관광자산")
    if not exact_partial:
        pdf.bullet("직접 매칭된 자산 없음")
    for row in exact_partial:
        pdf.bullet(
            short(
                f"{row['city']} / {row['official_name_ja']} / {row['display_name_ko']} "
                f"/ 제목근거={row['evidence_levels']} / 상세근거={row.get('tour_detail_evidence_levels', '해당 없음')}"
            )
        )
        pdf.text("  " + short(row["matched_product_titles"], 92), 8, 13, (0.42, 0.45, 0.50))

    pdf.h1("투어 상세 검증")
    if not detail_rows:
        pdf.bullet("상세 검증 대상 없음")
    for row in detail_rows:
        pdf.bullet(
            short(
                f"{row['anchor_name']} - {row['detail_evidence_level']} "
                f"({row['product_id']})"
            )
        )
        note = row["positive_evidence_excerpt"] or row["negative_evidence_excerpt"] or row["detail_status"]
        pdf.text("  " + short(note, 98), 8, 13, (0.42, 0.45, 0.50))

    pdf.new_page()
    pdf.h1("상품화 부족 자산 예시")
    for row in exact_gap[:18]:
        pdf.bullet(short(f"{row['city']} / {row['official_name_ja']} / {row['display_name_ko']} / {row['anchor_type']}"))

    pdf.h1("정확한 리스트 파일")
    pdf.bullet(f"supply_gap_exact_list.csv: {len(exact_rows)}개 1차 관광자산 원장")
    pdf.bullet(f"matched_assets_exact_list.csv: 직접 매칭된 {len(exact_partial)}개 부분 상품화 자산")
    pdf.bullet(f"under_connected_assets_exact_list.csv: 직접 매칭이 없는 {len(exact_gap)}개 상품화 부족 자산")
    pdf.bullet("tour_detail_evidence.csv: 투어 제목 후보의 상세/불포함/미노출 검증 원장")
    pdf.bullet("SUPPLY_GAP_EXACT_LIST.md / TOUR_DETAIL_EVIDENCE_REPORT.md: 사람이 읽기 좋은 보고서")

    pdf.save()
    print(PDF_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
