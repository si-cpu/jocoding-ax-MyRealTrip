#!/usr/bin/env python3
"""Render the first-pass T&A Supply Gap Map result as a PDF."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"
PDF_PATH = OUT / "ta_supply_gap_first_pass.pdf"
FONT_PATHS = [
    Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def register_fonts() -> tuple[str, str]:
    for font_path in FONT_PATHS:
        if not font_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("KoreanFont", str(font_path)))
            return "KoreanFont", "KoreanFont"
        except Exception:
            continue
    return "Helvetica", "Helvetica-Bold"


def para(text: str, style: ParagraphStyle) -> Paragraph:
    escaped = escape(text.replace("<br/>", "\n"))
    return Paragraph(escaped.replace("\n", "<br/>"), style)


def make_table(
    data: list[list[str]],
    widths: list[float],
    font_name: str,
    body_style: ParagraphStyle | None = None,
    header_bg=colors.HexColor("#eef3ff"),
) -> Table:
    if body_style:
        data = [[para(cell, body_style) for cell in row] for row in data]
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1d2a44")),
                ("BACKGROUND", (0, 0), (-1, 0), header_bg),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d9dee8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(doc.font_name, 8)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawString(18 * mm, 11 * mm, "T&A Supply Gap Map - First-pass result")
    canvas.drawRightString(192 * mm, 11 * mm, f"{doc.page}")
    canvas.restoreState()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    font_name, bold_name = register_fonts()

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleKo",
        parent=styles["Title"],
        fontName=bold_name,
        fontSize=24,
        leading=31,
        textColor=colors.HexColor("#111827"),
        alignment=TA_LEFT,
        spaceAfter=12,
    )
    subtitle = ParagraphStyle(
        "SubtitleKo",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=11,
        leading=17,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=18,
    )
    h1 = ParagraphStyle(
        "H1Ko",
        parent=styles["Heading1"],
        fontName=bold_name,
        fontSize=16,
        leading=22,
        textColor=colors.HexColor("#111827"),
        spaceBefore=10,
        spaceAfter=8,
    )
    body = ParagraphStyle(
        "BodyKo",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=16,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=8,
    )
    note = ParagraphStyle(
        "NoteKo",
        parent=body,
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#6b7280"),
    )
    table_text = ParagraphStyle(
        "TableTextKo",
        parent=body,
        fontName=font_name,
        fontSize=8,
        leading=12,
        spaceAfter=0,
    )
    callout = ParagraphStyle(
        "CalloutKo",
        parent=body,
        fontName=font_name,
        fontSize=11,
        leading=17,
        leftIndent=8,
        rightIndent=8,
        borderColor=colors.HexColor("#c7d2fe"),
        borderWidth=0.8,
        borderPadding=8,
        backColor=colors.HexColor("#f5f7ff"),
        spaceBefore=8,
        spaceAfter=12,
    )

    matches = read_csv(ROOT / "data" / "supply_gap_analysis" / "official_mcp_anchor_matches.csv")
    scores = read_csv(ROOT / "data" / "supply_gap_analysis" / "supply_gap_scores.csv")
    exact_rows = read_csv(ROOT / "data" / "supply_gap_analysis" / "exports" / "supply_gap_exact_list.csv")
    mcp_rows = read_csv(ROOT / "data" / "mcp_tna_products" / "processed" / "mcp_tna_products.csv")
    anchors = read_csv(ROOT / "data" / "official_tourism_sources" / "anchors" / "official_experience_anchors.csv")

    partial = [r for r in scores if r["classification"] == "부분 상품화 자산"]
    gap = [r for r in scores if r["classification"] == "상품화 부족 자산"]
    exact_partial = [r for r in exact_rows if r["classification"] == "부분 상품화 자산"]
    exact_gap = [r for r in exact_rows if r["classification"] == "상품화 부족 자산"]
    fukuoka = [r for r in scores if r["city_id"] == "jp-fukuoka"]
    hiroshima = [r for r in scores if r["city_id"] == "jp-hiroshima"]

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    doc.font_name = font_name

    story = []
    story.append(para("T&A Supply Gap Map", title))
    story.append(para("1차 결과 리포트 - 공식 관광자산 대비 마이리얼트립 상품화 연결 상태", subtitle))
    story.append(
        para(
            f"생성일: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M')}<br/>"
            "목적: 실제 관광객 인기 예측이 아니라, 공식 관광자산과 MCP 상품 샘플 사이의 상품화 공백을 찾는 BD 분석.",
            note,
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        make_table(
            [
                ["지표", "1차 결과"],
                ["공식 원천 앵커", f"{len(anchors)}개"],
                ["대표 분석 대상", f"{len(scores)}개"],
                ["식음/야타이 후보", f"{len(anchors) - len(scores)}개"],
                ["MCP 상품 샘플", f"{len(mcp_rows)}개"],
                ["직접 매칭", f"{len(matches)}개"],
                ["부분 상품화 자산", f"{len(partial)}개"],
                ["상품화 부족 자산", f"{len(gap)}개"],
            ],
            [70 * mm, 90 * mm],
            font_name,
            table_text,
        )
    )
    story.append(Spacer(1, 12))
    story.append(
        para(
            "핵심 해석: 이 결과는 '수요가 없다'가 아니라 '현재 수집된 마이리얼트립 상품 샘플에서 공식 관광자산과 직접 연결되는 표현이 약하다'는 뜻이다.",
            callout,
        )
    )
    story.append(
        para(
            "정확한 전체 리스트는 별도 원장 파일로 제공된다: data/supply_gap_analysis/exports/supply_gap_exact_list.csv",
            note,
        )
    )

    story.append(para("도시별 상품화 상태", h1))
    city_table = [
        ["도시", "부분 상품화", "상품화 부족", "해석"],
        [
            "히로시마",
            str(sum(1 for r in hiroshima if r["classification"] == "부분 상품화 자산")),
            str(sum(1 for r in hiroshima if r["classification"] == "상품화 부족 자산")),
            "히로시마성/평화기념관은 연결됨. 나머지는 별칭/일정 상세 매칭 필요",
        ],
    ]
    story.append(make_table(city_table, [24 * mm, 23 * mm, 23 * mm, 92 * mm], font_name, table_text))

    story.append(PageBreak())
    story.append(para("직접 매칭된 공식 관광자산", h1))
    rows = [["공식명(JA)", "표시명(KO)", "근거 등급", "연결 상품"]]
    for r in exact_partial:
        rows.append([r["official_name_ja"], r["display_name_ko"], r["evidence_levels"], r["matched_product_titles"]])
    story.append(make_table(rows, [35 * mm, 34 * mm, 32 * mm, 61 * mm], font_name, table_text))
    story.append(Spacer(1, 12))
    story.append(
        para(
            "이번 개선에서 중요한 발견은 공식 일본어명과 한국어 상품명 사이의 불일치다. 예를 들어 공식 데이터의 '広島城'은 상품 제목에서 '히로시마성'으로 나타난다. 단, 투어 상품은 제목 매칭만으로 방문을 확정하지 않고 상세 일정 확인이 필요하다. 입장권은 상품 자체가 해당 시설 이용권이므로 제목/상품명 매칭을 강한 근거로 본다.",
            body,
        )
    )

    story.append(para("현재 가장 강한 BD 시그널", h1))
    story.append(
        para(
            "후쿠오카 공식 야타이 데이터는 107개 개별 점포를 제공한다. 대표 분석에서는 판매 형식이 아니라 '福岡市 屋台'라는 장소군 앵커를 기준으로 본다. 포장마차 투어는 투어라는 형식이 아니라 야타이 장소군에 연결되는 상품화 후보로 해석한다. 개별 점포는 파트너 후보 원장으로 따로 관리한다.",
            body,
        )
    )

    story.append(PageBreak())
    story.append(para("상품화 부족 자산을 읽는 방법", h1))
    story.append(
        para(
            "상품화 부족 자산은 현재 샘플에서 직접 상품 매칭이 없다는 뜻이다. 관광객이 적다거나 상업적 가치가 없다는 뜻이 아니다. 다음 액션은 더 많은 MCP 카테고리 수집, 별칭 추가, 투어 상세 일정 확인, 수동 검증이다.",
            body,
        )
    )
    top_gaps = exact_gap[:12]
    rows = [["도시", "공식명(JA)", "표시명(KO)", "MCP 대응", "유형"]]
    for r in top_gaps:
        rows.append([r["city"], r["official_name_ja"], r["display_name_ko"], r["mcp_one_to_one_status"], r["anchor_type"]])
    story.append(make_table(rows, [22 * mm, 48 * mm, 32 * mm, 28 * mm, 32 * mm], font_name, table_text))

    story.append(para("다음 단계", h1))
    story.append(
        para(
            "1. MCP 수집을 도시/카테고리 단위로 나누어 rate limit을 줄인다.<br/>"
            "2. 공식 일본어명과 한국어 상품명 별칭 사전을 확장한다.<br/>"
            "3. 제목 매칭 이후 투어 상세 일정까지 조회해 포함 관광지를 확인한다.<br/>"
            "4. 도시별 공급 집중도와 공급 공백 TOP 리스트를 자동 생성한다.",
            body,
        )
    )
    story.append(Spacer(1, 8))
    story.append(para("정확한 리스트 파일", h1))
    story.append(
        make_table(
            [
                ["파일", "내용"],
                ["supply_gap_exact_list.csv", "172개 공식 관광자산 전체 원장"],
                ["matched_assets_exact_list.csv", "직접 매칭된 3개 부분 상품화 자산"],
                ["under_connected_assets_exact_list.csv", "직접 매칭이 없는 169개 상품화 부족 자산"],
                ["SUPPLY_GAP_EXACT_LIST.md", "사람이 읽기 좋은 전체 리스트 보고서"],
            ],
            [65 * mm, 97 * mm],
            font_name,
            table_text,
        )
    )

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(PDF_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
