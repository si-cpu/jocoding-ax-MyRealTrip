PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cities (
  id TEXT PRIMARY KEY,
  country TEXT NOT NULL,
  name TEXT NOT NULL,
  positioning TEXT NOT NULL,
  demand_signal TEXT NOT NULL,
  is_mvp_city INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS experiences (
  id TEXT PRIMARY KEY,
  city_id TEXT NOT NULL REFERENCES cities(id),
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  evidence TEXT NOT NULL,
  products INTEGER NOT NULL DEFAULT 0,
  repeats INTEGER NOT NULL DEFAULT 0,
  price_band TEXT NOT NULL,
  business_hint TEXT NOT NULL,
  is_representative INTEGER NOT NULL DEFAULT 0,
  is_hidden_choice INTEGER NOT NULL DEFAULT 0,
  is_productization_candidate INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS experience_tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  experience_id TEXT NOT NULL REFERENCES experiences(id),
  tag TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS purchase_methods (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  experience_id TEXT NOT NULL REFERENCES experiences(id),
  method TEXT NOT NULL,
  method_type TEXT NOT NULL,
  is_primary INTEGER NOT NULL DEFAULT 0,
  user_note TEXT
);

CREATE TABLE IF NOT EXISTS official_data_sources (
  id TEXT PRIMARY KEY,
  country TEXT NOT NULL,
  city_id TEXT NOT NULL REFERENCES cities(id),
  source_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  base_url TEXT NOT NULL,
  license TEXT,
  requires_api_key INTEGER NOT NULL DEFAULT 0,
  update_cycle TEXT,
  last_checked_at TEXT,
  priority INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS official_assets (
  id TEXT PRIMARY KEY,
  city_id TEXT NOT NULL REFERENCES cities(id),
  source_id TEXT NOT NULL REFERENCES official_data_sources(id),
  asset_type TEXT NOT NULL,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  address TEXT,
  lat REAL,
  lng REAL,
  official_url TEXT,
  description TEXT,
  is_certified INTEGER NOT NULL DEFAULT 0,
  certification_type TEXT,
  last_collected_at TEXT
);

CREATE TABLE IF NOT EXISTS experience_source_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  experience_id TEXT NOT NULL REFERENCES experiences(id),
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_record_id TEXT,
  confidence REAL NOT NULL DEFAULT 0.7,
  evidence_text TEXT
);

CREATE TABLE IF NOT EXISTS anchor_generation_runs (
  id TEXT PRIMARY KEY,
  source_snapshot_path TEXT NOT NULL,
  generated_path TEXT NOT NULL,
  rule_version TEXT NOT NULL,
  total_records INTEGER NOT NULL DEFAULT 0,
  accepted_candidates INTEGER NOT NULL DEFAULT 0,
  review_candidates INTEGER NOT NULL DEFAULT 0,
  rejected_candidates INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS generated_anchor_candidates (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES anchor_generation_runs(id),
  city_id TEXT NOT NULL REFERENCES cities(id),
  source_type TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  raw_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  category TEXT NOT NULL,
  anchor_type TEXT NOT NULL,
  confidence REAL NOT NULL,
  automation_status TEXT NOT NULL,
  reason TEXT NOT NULL,
  product_signal INTEGER NOT NULL DEFAULT 0,
  official_signal INTEGER NOT NULL DEFAULT 0,
  repeats_signal INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS accommodation_candidates (
  id TEXT PRIMARY KEY,
  city_id TEXT NOT NULL REFERENCES cities(id),
  source_type TEXT NOT NULL,
  source_id TEXT,
  area_name TEXT NOT NULL,
  accommodation_type TEXT NOT NULL,
  decision_reason TEXT NOT NULL,
  risk_signal TEXT,
  breakfast_available INTEGER NOT NULL DEFAULT 0,
  smoking_policy_signal TEXT,
  bedding_signal TEXT,
  price_band TEXT,
  product_count INTEGER NOT NULL DEFAULT 0,
  collection_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trips (
  id TEXT PRIMARY KEY,
  city_id TEXT NOT NULL REFERENCES cities(id),
  trip_title TEXT NOT NULL,
  travel_party_type TEXT NOT NULL,
  privacy_mode TEXT NOT NULL,
  start_date TEXT,
  end_date TEXT,
  story_generated INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS stamps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id TEXT NOT NULL REFERENCES trips(id),
  experience_id TEXT NOT NULL REFERENCES experiences(id),
  stamp_status TEXT NOT NULL,
  photo_mode TEXT NOT NULL,
  memo_mode TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trip_timeline_events (
  id TEXT PRIMARY KEY,
  trip_id TEXT NOT NULL REFERENCES trips(id),
  city_id TEXT NOT NULL REFERENCES cities(id),
  experience_id TEXT REFERENCES experiences(id),
  event_type TEXT NOT NULL,
  label TEXT NOT NULL,
  initial_recorded_at TEXT,
  user_selected_time TEXT,
  time_status TEXT NOT NULL,
  sequence_order INTEGER NOT NULL,
  source_type TEXT NOT NULL,
  is_user_confirmed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS event_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  city_id TEXT REFERENCES cities(id),
  event_name TEXT NOT NULL,
  step_name TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS funnel_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  city_id TEXT NOT NULL REFERENCES cities(id),
  step_name TEXT NOT NULL,
  started_count INTEGER NOT NULL DEFAULT 0,
  completed_count INTEGER NOT NULL DEFAULT 0,
  dropoff_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS error_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  city_id TEXT REFERENCES cities(id),
  step_name TEXT NOT NULL,
  error_type TEXT NOT NULL,
  user_safe_message TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id TEXT NOT NULL REFERENCES trips(id),
  experience_id TEXT REFERENCES experiences(id),
  rating INTEGER,
  recommend_intent TEXT,
  discomfort_type TEXT,
  skipped INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS trip_decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id TEXT NOT NULL REFERENCES trips(id),
  decision_status TEXT NOT NULL,
  reason_category TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trip_budget_estimates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id TEXT NOT NULL REFERENCES trips(id),
  transport_cost INTEGER NOT NULL DEFAULT 0,
  accommodation_cost INTEGER NOT NULL DEFAULT 0,
  activity_cost INTEGER NOT NULL DEFAULT 0,
  food_cost_range TEXT,
  source_type TEXT NOT NULL
);
