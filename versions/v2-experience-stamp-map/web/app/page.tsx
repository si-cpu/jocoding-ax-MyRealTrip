"use client";

import { useMemo, useState } from "react";
import demoData from "../data/demo-data.json";

type City = {
  id: string;
  country: "한국" | "일본";
  name: string;
  positioning: string;
  demandSignal: string;
  experiences: Experience[];
};

type Experience = {
  id: string;
  title: string;
  category: "뭐 하지" | "뭐 먹지" | "도시 내 이동";
  evidence: "공식 상품" | "지역 공식 자산" | "상품화 후보";
  products: number;
  repeats: number;
  priceBand: string;
  tags: string[];
  purchaseMethods: string[];
  businessHint: string;
  officialAssets: {
    id: string;
    asset_type: string;
    name: string;
    category: string;
    lat: number | null;
    lng: number | null;
    official_url: string | null;
    confidence: number;
  }[];
};

type TimelineItem = {
  id: string;
  type: string;
  label: string;
  time: string;
  status: "초깃값" | "사용자 확정" | "시간 미정";
};

type AccommodationCandidate = {
  id: string;
  city_id: string;
  source_type: string;
  area_name: string;
  accommodation_type: string;
  decision_reason: string;
  risk_signal: string | null;
  breakfast_available: number;
  smoking_policy_signal: string | null;
  bedding_signal: string | null;
  price_band: string | null;
  product_count: number;
  collection_status: string;
};

type AnchorAutomation = {
  latestRun: {
    id: string;
    rule_version: string;
    total_records: number;
    accepted_candidates: number;
    review_candidates: number;
    rejected_candidates: number;
    created_at: string;
  } | null;
  candidates: {
    id: string;
    city_id: string;
    raw_name: string;
    normalized_name: string;
    category: Experience["category"];
    anchor_type: string;
    confidence: number;
    automation_status: "AUTO_ACCEPT" | "NEEDS_REVIEW" | "REJECTED";
    reason: string;
  }[];
};

type RouteMode = "walk" | "transit";

const cities = demoData.cities as City[];
const citySet = demoData.citySet;
const accommodationCandidates = demoData.accommodationCandidates as AccommodationCandidate[];
const anchorAutomation = demoData.anchorAutomation as AnchorAutomation;
const steps = [
  { id: "city", label: "1. 도시", title: "어디로 갈까?" },
  { id: "experience", label: "2. 경험", title: "무엇을 담을까?" },
  { id: "method", label: "3. 방식", title: "어떻게 이용할까?" },
  { id: "timeline", label: "4. 일정", title: "언제 움직일까?" },
  { id: "story", label: "5. 스토리", title: "어떻게 남길까?" },
  { id: "report", label: "내부 리포트", title: "사업개발자는 무엇을 볼까?" }
] as const;

type StepId = (typeof steps)[number]["id"];

function makeInitialTimeline(city: City, selected: string[]): TimelineItem[] {
  const selectedExperiences = city.experiences.filter((experience) => selected.includes(experience.id));
  const base: TimelineItem[] = [
    {
      id: "arrival",
      type: city.country === "일본" ? "공항" : "역",
      label: city.country === "일본" ? `${city.name} 공항 도착` : `${city.name}역 도착`,
      time: "10:00",
      status: "초깃값"
    },
    {
      id: "stay",
      type: "숙소",
      label: `${city.name} 숙소 체크인 또는 짐 보관`,
      time: "12:00",
      status: "초깃값"
    }
  ];

  const experienceItems = selectedExperiences.map((experience, index) => ({
    id: experience.id,
    type: experience.category === "뭐 먹지" ? "먹거리" : experience.category === "도시 내 이동" ? "이동" : "여행지",
    label: experience.title,
    time: `${14 + index * 2}:00`,
    status: "초깃값" as const
  }));

  return [
    ...base,
    ...experienceItems,
    {
      id: "story",
      type: "스토리",
      label: "오늘의 여행 스토리 정리",
      time: "21:00",
      status: "시간 미정"
    }
  ];
}

export default function Home() {
  const [cityId, setCityId] = useState("osaka");
  const [filter, setFilter] = useState<Experience["category"]>("뭐 하지");
  const [selected, setSelected] = useState<string[]>(["usj", "harukas"]);
  const [partyType, setPartyType] = useState("개인 여행");
  const [privacyMode, setPrivacyMode] = useState("사진 없이 글로 대체");
  const [timeline, setTimeline] = useState<TimelineItem[]>(() => makeInitialTimeline(cities[0], ["usj", "harukas"]));
  const [activeStep, setActiveStep] = useState<StepId>("city");
  const [routeMode, setRouteMode] = useState<RouteMode>("walk");

  const city = cities.find((item) => item.id === cityId) ?? cities[0];
  const automationForCity = anchorAutomation.candidates.filter((candidate) => candidate.city_id === city.id);

  const visibleExperiences = useMemo(() => {
    return city.experiences.filter((experience) => experience.category === filter);
  }, [city, filter]);

  const selectedExperiences = city.experiences.filter((experience) => selected.includes(experience.id));
  const cityAccommodations = accommodationCandidates.filter((candidate) => candidate.city_id === city.id);

  const switchCity = (nextId: string) => {
    const nextCity = cities.find((item) => item.id === nextId) ?? cities[0];
    const defaults = nextCity.experiences.slice(0, 2).map((experience) => experience.id);
    setCityId(nextId);
    setSelected(defaults);
    setTimeline(makeInitialTimeline(nextCity, defaults));
    setActiveStep("experience");
  };

  const toggleExperience = (experienceId: string) => {
    const nextSelected = selected.includes(experienceId)
      ? selected.filter((item) => item !== experienceId)
      : [...selected, experienceId];
    setSelected(nextSelected);
    setTimeline(makeInitialTimeline(city, nextSelected));
  };

  const updateTime = (id: string, time: string) => {
    setTimeline((items) =>
      items.map((item) =>
        item.id === id
          ? {
              ...item,
              time,
              status: time ? "사용자 확정" : "시간 미정"
            }
          : item
      )
    );
  };

  const report = {
    cityViews: 1284,
    selectedRate: `${Math.round((selectedExperiences.length / Math.max(city.experiences.length, 1)) * 100)}%`,
    timelineRate: `${timeline.filter((item) => item.status === "사용자 확정").length}/${timeline.length}`,
    productCoverage: `${city.experiences.filter((experience) => experience.evidence === "공식 상품").length}/${city.experiences.length}`,
    hidden: city.experiences.filter((experience) => experience.products <= 2).length,
    costBand: selectedExperiences.map((experience) => experience.priceBand).join(" · ") || "미정",
    automationAccepted: automationForCity.filter((candidate) => candidate.automation_status === "AUTO_ACCEPT").length,
    automationReview: automationForCity.filter((candidate) => candidate.automation_status === "NEEDS_REVIEW").length,
    automationRejected: automationForCity.filter((candidate) => candidate.automation_status === "REJECTED").length
  };

  const focusExperience = selectedExperiences[0] ?? city.experiences[0];
  const routeStops = timeline.filter((item) => item.id !== "story");
  const routeSummary =
    routeMode === "walk"
      ? { label: "도보 중심", duration: `${Math.max(routeStops.length - 1, 1) * 18}분`, cost: "교통비 0원", note: "가까운 경험을 묶어 걷기 좋은 순서로 봅니다." }
      : { label: "대중교통 중심", duration: `${Math.max(routeStops.length - 1, 1) * 11}분`, cost: "교통비 약 1,800~4,500원", note: "역·버스 정류장 기준으로 이동 부담을 줄입니다." };

  return (
    <main className="page">
      <section className="hero">
        <div className="hero-card">
          <span className="eyebrow">MyRealTrip T&A Portfolio MVP</span>
          <h1>도시의 매력을 먼저 보고, 상품은 나중에 고른다.</h1>
          <p>
            1차 MVP는 오사카·후쿠오카·부산 3개 도시의 장소·음식·시설 앵커를 지도처럼 펼치고, 사용자가 고른 앵커를
            도시 내 이동·숙소 후보·여행지 타임라인과 스탬프로 연결합니다. 사진이나 위치 기록을 강요하지 않고,
            선택형 데이터만 내부 사업개발 인사이트로 집계합니다.
          </p>
          <div className="hero-actions">
            <button className="primary" onClick={() => setActiveStep("city")}>
              여행 설계 시작
            </button>
            <button className="secondary" onClick={() => setActiveStep("report")}>
              내부 리포트 구조 보기
            </button>
          </div>
        </div>

        <aside className="hero-side panel">
          <div className="metric-card">
            <strong>{citySet.length}</strong>
            <span>{citySet.join(" · ")}</span>
          </div>
          <div className="metric-card">
            <strong>0 GPS</strong>
            <span>실시간 위치추적 없이 사용자 선택 시간만 일정에 반영</span>
          </div>
          <div className="metric-card">
            <strong>Skip OK</strong>
            <span>사진·메모·피드백·공유는 모두 건너뛰거나 글로 대체 가능</span>
          </div>
        </aside>
      </section>

      <nav className="step-nav" aria-label="여행 설계 단계">
        {steps.map((step) => (
          <button className={`step-button ${activeStep === step.id ? "active" : ""}`} key={step.id} onClick={() => setActiveStep(step.id)}>
            <span>{step.label}</span>
            <b>{step.title}</b>
          </button>
        ))}
      </nav>

      <section className="flow-shell" id="map">
        <div className="flow-header">
          <span className="eyebrow">{steps.find((step) => step.id === activeStep)?.label}</span>
          <h2>{steps.find((step) => step.id === activeStep)?.title}</h2>
          <p>
            한 번에 하나씩만 결정합니다. 상품 목록을 먼저 밀어 넣지 않고, 도시의 매력과 선택지를 좁혀가며 여행을 완성합니다.
          </p>
        </div>

        {activeStep === "city" && (
        <section className="step-layout single">
          <div className="panel">
          <h2>도시 선택</h2>
          <p className="panel-copy">1차 MVP는 데이터 성격이 다른 도시 3곳으로 먼저 검증합니다. 이후 같은 구조로 광역시급 도시 세트까지 확장합니다.</p>
          <div className="city-list">
            {cities.map((item) => (
              <button
                className={`city-button ${item.id === city.id ? "active" : ""}`}
                key={item.id}
                onClick={() => switchCity(item.id)}
              >
                <b>
                  {item.name} · {item.country}
                </b>
                <span>{item.positioning}</span>
              </button>
            ))}
          </div>
          <div className="step-actions">
            <button className="primary" onClick={() => setActiveStep("experience")}>이 도시에서 할 일 보기</button>
          </div>
          </div>
        </section>
        )}

        {activeStep === "experience" && (
        <section className="step-layout">
        <div className="panel">
          <h2>{city.name} 앵커 지도</h2>
          <p className="panel-copy">
            투어명 그대로가 아니라 사용자가 먼저 “가야겠다”라고 고르는 장소·음식·시설 단위로 재배열합니다.
            많이 검증된 앵커와 덜 노출된 선택지를 함께 보여줘 상품 피로감을 줄입니다.
          </p>

          <div className="tabs">
            {(["뭐 하지", "뭐 먹지", "도시 내 이동"] as const).map((tab) => (
              <button className={`chip ${filter === tab ? "active" : ""}`} key={tab} onClick={() => setFilter(tab)}>
                {tab}
              </button>
            ))}
          </div>

          <div className="method-panel">
            <div>
              <span className="eyebrow">선택 경험 구매방식 비교</span>
              <h3>{focusExperience.title}</h3>
              <p className="panel-copy">
                사용자는 먼저 장소·음식·시설 앵커를 고르고, 그 다음에 단독 입장권·패스·투어·지역 자산 중 가능한 방식을 비교합니다.
              </p>
            </div>
            <div className="method-grid">
              {focusExperience.purchaseMethods.map((method) => (
                <div className="method-card" key={method}>
                  {method}
                </div>
              ))}
            </div>
            <p className="business-hint">{focusExperience.businessHint}</p>
          </div>

          <div className="experience-list">
            {visibleExperiences.map((experience) => (
              <article className={`experience-card ${selected.includes(experience.id) ? "selected" : ""}`} key={experience.id}>
                <div>
                  <h3>{experience.title}</h3>
                  <p className="panel-copy">
                    {experience.evidence} · 연결 상품 {experience.products}개 · 반복 근거 {experience.repeats}회 · {experience.priceBand}
                  </p>
                  {experience.officialAssets.length > 0 && (
                    <p className="asset-line">
                      공식 자산 {experience.officialAssets.length}개 연결 · {experience.officialAssets.map((asset) => asset.name).join(", ")}
                    </p>
                  )}
                  <div className="tags">
                    {experience.tags.map((tag) => (
                      <span className={`tag ${tag.includes("대표") || tag.includes("TOP") ? "strong" : ""}`} key={tag}>
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <button className="ghost" onClick={() => toggleExperience(experience.id)}>
                  {selected.includes(experience.id) ? "담김" : "담기"}
                </button>
              </article>
            ))}
          </div>
          <div className="step-actions">
            <button className="secondary" onClick={() => setActiveStep("city")}>도시 다시 선택</button>
            <button className="primary" onClick={() => setActiveStep("method")}>구매방식 비교</button>
          </div>
        </div>

        <aside className="panel compact-side">
          <h2>스탬프 & 기록</h2>
          <p className="panel-copy">사진을 올리지 않아도 됩니다. 글로 대체하거나, 기록 자체를 건너뛰어도 여정은 이어집니다.</p>

          <div className="control-row">
            <select className="select" value={partyType} onChange={(event) => setPartyType(event.target.value)}>
              <option>개인 여행</option>
              <option>단체 여행</option>
              <option>가족 여행</option>
            </select>
            <select className="select" value={privacyMode} onChange={(event) => setPrivacyMode(event.target.value)}>
              <option>사진 없이 글로 대체</option>
              <option>사진 유형만 선택</option>
              <option>비공개 저장</option>
              <option>기록 건너뛰기</option>
            </select>
          </div>

          <div className="stamp-board">
            {selectedExperiences.map((experience) => (
              <div className="stamp" key={experience.id}>
                {experience.title}
              </div>
            ))}
          </div>

          <div className="privacy-note">
            내부 리포트에는 사진 원본, 원문 메모, 개별 여행 스토리가 들어가지 않습니다. 숙소는 경험 카드에 섞지 않고 MCP 숙소 후보로 별도 수집합니다.
          </div>

          <div className="lodging-panel">
            <span className="eyebrow">MCP 숙소 후보</span>
            <h3>숙소는 별도 비교</h3>
            {cityAccommodations.slice(0, 2).map((candidate) => (
              <div className="lodging-card" key={candidate.id}>
                <b>{candidate.area_name} · {candidate.accommodation_type}</b>
                <span>{candidate.price_band} · 조식 {candidate.breakfast_available ? "확인" : "미확인"} · 후보 {candidate.product_count}개</span>
                <p>{candidate.decision_reason}</p>
              </div>
            ))}
          </div>
        </aside>
        </section>
        )}

        {activeStep === "method" && (
        <section className="step-layout single">
          <div className="method-panel large">
            <div>
              <span className="eyebrow">선택 경험 구매방식 비교</span>
              <h3>{focusExperience.title}</h3>
              <p className="panel-copy">
                사용자는 먼저 장소·음식·시설 앵커를 고르고, 그 다음에 단독 입장권·패스·투어·지역 자산 중 가능한 방식을 비교합니다.
              </p>
            </div>
            <div className="method-grid">
              {focusExperience.purchaseMethods.map((method) => (
                <div className="method-card" key={method}>
                  {method}
                </div>
              ))}
            </div>
            <p className="business-hint">{focusExperience.businessHint}</p>
            <div className="step-actions inverted">
              <button className="secondary" onClick={() => setActiveStep("experience")}>경험 다시 고르기</button>
              <button className="primary" onClick={() => setActiveStep("timeline")}>타임라인 만들기</button>
            </div>
          </div>
        </section>
        )}

        {activeStep === "timeline" && (
        <section className="step-layout">
        <div className="panel">
          <h2>여행 타임라인</h2>
          <p className="panel-copy">
            최초에는 저장 시각을 초깃값으로 넣지만, 사용자가 직접 여행 일정 시간으로 조정합니다. 비어 있어도 괜찮습니다.
          </p>
          <div className="route-toggle" aria-label="이동 방식 선택">
            <button className={routeMode === "walk" ? "active" : ""} onClick={() => setRouteMode("walk")}>걷는 코스</button>
            <button className={routeMode === "transit" ? "active" : ""} onClick={() => setRouteMode("transit")}>버스/지하철 코스</button>
          </div>
          <div className="timeline-list">
            {timeline.map((item) => (
              <div className="timeline-item" key={item.id}>
                <div className="time-box">
                  <input
                    aria-label={`${item.label} 일정 시간`}
                    type="time"
                    value={item.time}
                    onChange={(event) => updateTime(item.id, event.target.value)}
                  />
                  <span className="tag">{item.status}</span>
                  <button className="mini-button" onClick={() => updateTime(item.id, "")}>
                    시간 비우기
                  </button>
                </div>
                <div>
                  <div className="timeline-title">{item.label}</div>
                  <p className="panel-copy">
                    {item.type} · 사용자가 확정한 시간만 스토리에 반영 · GPS/실시간 이동 경로 없음
                  </p>
                </div>
              </div>
            ))}
          </div>
          <div className="step-actions">
            <button className="secondary" onClick={() => setActiveStep("method")}>구매방식으로 돌아가기</button>
            <button className="primary" onClick={() => setActiveStep("story")}>스토리 만들기</button>
          </div>
        </div>

        <aside className="panel compact-side">
          <h2>동선 지도</h2>
          <p className="panel-copy">
            Google Maps API 연동 전에는 샘플 좌표 기반 프리뷰로 보여줍니다. 실제 연결 시 전 세계 도시의 도보·대중교통 경로를 같은 구조로 표시합니다.
          </p>
          <div className={`map-preview ${routeMode}`}>
            <div className="map-grid-lines" />
            <div className="route-line" />
            {routeStops.map((item, index) => (
              <div className={`map-pin pin-${index + 1}`} key={item.id}>
                <span>{index + 1}</span>
                <b>{item.label}</b>
              </div>
            ))}
          </div>
          <div className="route-summary">
            <div>
              <span>이동 방식</span>
              <strong>{routeSummary.label}</strong>
            </div>
            <div>
              <span>예상 이동 시간</span>
              <strong>{routeSummary.duration}</strong>
            </div>
            <div>
              <span>예상 교통비</span>
              <strong>{routeSummary.cost}</strong>
            </div>
          </div>
          <p className="privacy-note">
            {routeSummary.note} 위치추적이 아니라 사용자가 선택한 일정 앵커만 지도에 배치합니다.
          </p>
        </aside>
        </section>
        )}

        {activeStep === "story" && (
        <section className="step-layout">
        <div className="panel">
          <h2>공유용 여행 스토리</h2>
          <p className="panel-copy">상품명이 아니라 내가 고른 경험과 시간 흐름으로 여행을 요약합니다.</p>
          <div className="story-card">
            <strong>
              {city.name}에서 완성한 {partyType}
            </strong>
            <p>
              {timeline
                .filter((item) => item.status !== "시간 미정")
                .map((item) => `${item.time} ${item.label}`)
                .join(" → ") || `${city.name}에서 아직 시간을 정하지 않은 느슨한 여행입니다.`}
            </p>
            <p>기록 방식: {privacyMode}. 공유 전에는 공개 범위를 다시 확인합니다.</p>
          </div>
          <div className="step-actions">
            <button className="secondary" onClick={() => setActiveStep("timeline")}>시간 다시 조정</button>
            <button className="primary" onClick={() => setActiveStep("city")}>다른 도시 보기</button>
          </div>
        </div>

        <aside className="panel compact-side">
          <h2>선택 요약</h2>
          <p className="panel-copy">{selectedExperiences.length}개의 경험이 스탬프 보드에 담겼습니다.</p>
          <div className="stamp-board">
            {selectedExperiences.map((experience) => (
              <div className="stamp" key={experience.id}>{experience.title}</div>
            ))}
          </div>
        </aside>
        </section>
        )}

        {activeStep === "report" && (
        <section className="step-layout single">
        <div className="panel" id="report">
          <h2>내부 사업개발 리포트</h2>
          <p className="panel-copy">일반 사용자는 볼 수 없습니다. 개인 기록이 아니라 집계 지표만 저장합니다.</p>
          <div className="report-list">
            <div className="report-row">
              <span>도시 조회량</span>
              <strong>{report.cityViews.toLocaleString()}회</strong>
            </div>
            <div className="report-row">
              <span>경험 선택률</span>
              <strong>{report.selectedRate}</strong>
            </div>
            <div className="report-row">
              <span>타임라인 확정</span>
              <strong>{report.timelineRate}</strong>
            </div>
            <div className="report-row">
              <span>공식 상품 커버리지</span>
              <strong>{report.productCoverage}</strong>
            </div>
            <div className="report-row">
              <span>숨은 선택지 후보</span>
              <strong>{report.hidden}개</strong>
            </div>
            <div className="report-row">
              <span>예상 비용 신호</span>
              <strong>{report.costBand}</strong>
            </div>
            <div className="report-row">
              <span>자동 앵커 후보</span>
              <strong>{report.automationAccepted} 자동 · {report.automationReview} 검수 · {report.automationRejected} 제외</strong>
            </div>
          </div>
          <div className="automation-panel">
            <div>
              <span className="eyebrow">Anchor automation</span>
              <h3>원천 데이터 → 후보 생성 → 검수</h3>
              <p className="panel-copy">
                MCP 상품명과 공식 자산명을 그대로 보여주지 않고, 판매 문구·검증 조건·숙소·버스 항목을 규칙으로 분리합니다.
              </p>
            </div>
            <div className="automation-list">
              {automationForCity.slice(0, 5).map((candidate) => (
                <div className={`automation-item ${candidate.automation_status.toLowerCase().replace("_", "-")}`} key={candidate.id}>
                  <b>{candidate.normalized_name}</b>
                  <span>{candidate.automation_status} · {candidate.category} · 신뢰도 {Math.round(candidate.confidence * 100)}%</span>
                  <p>{candidate.reason}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="step-actions">
            <button className="secondary" onClick={() => setActiveStep("city")}>사용자 화면으로 돌아가기</button>
          </div>
        </div>
      </section>
        )}
      </section>
    </main>
  );
}
