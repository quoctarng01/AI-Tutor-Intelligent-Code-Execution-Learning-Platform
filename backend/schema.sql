-- exercises (static content, seeded from JSON)
CREATE TABLE exercises (
id VARCHAR(20) PRIMARY KEY, -- e.g. "loops_003"
topic VARCHAR(50) NOT NULL,
subtopic VARCHAR(50),
title VARCHAR(200) NOT NULL,
difficulty SMALLINT CHECK (difficulty BETWEEN 1 AND 5),
problem_statement TEXT NOT NULL,
hint_l1 TEXT NOT NULL, -- pre-authored, safe
hint_l2 TEXT NOT NULL, -- pre-authored, safe
llm_context TEXT NOT NULL, -- injected into LLM prompt; NO answer
concept VARCHAR(200) NOT NULL,
correct_criteria JSONB NOT NULL, -- {type, test_cases} or {type, rubric}
prerequisite_ids TEXT[],
common_mistakes TEXT[],
tags TEXT[]
);

-- sessions (one row per student login)
CREATE TABLE sessions (
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
username VARCHAR(100) NOT NULL,
group_type VARCHAR(10) CHECK (group_type IN ('tutor','control')),
started_at TIMESTAMPTZ DEFAULT NOW(),
ended_at TIMESTAMPTZ
);

-- attempts (every answer submission)
CREATE TABLE attempts (
id BIGSERIAL PRIMARY KEY,
session_id UUID REFERENCES sessions(id),
exercise_id VARCHAR(20) REFERENCES exercises(id),
submitted_code TEXT NOT NULL,
is_correct BOOLEAN NOT NULL,
hints_used SMALLINT DEFAULT 0,
time_to_solve_s INTEGER,
hint_state VARCHAR(20) NOT NULL,
submitted_at TIMESTAMPTZ DEFAULT NOW()
);

-- hint_state: authoritative server-side state machine
-- ONE row per (session_id, exercise_id) — never derive level from hint_logs
CREATE TABLE hint_state (
session_id UUID REFERENCES sessions(id),
exercise_id VARCHAR(20) REFERENCES exercises(id),
current_level SMALLINT DEFAULT 0, -- 0=IDLE, 1-4=HINT_N, 5=EXHAUSTED
is_solved BOOLEAN DEFAULT FALSE,
opened_at TIMESTAMPTZ DEFAULT NOW(),
PRIMARY KEY (session_id, exercise_id)
);

-- hint_logs: every hint delivery — source data for rubric scoring
CREATE TABLE hint_logs (
id BIGSERIAL PRIMARY KEY,
session_id UUID REFERENCES sessions(id),
exercise_id VARCHAR(20) REFERENCES exercises(id),
hint_level SMALLINT NOT NULL, -- 1-4
prompt_version VARCHAR(20) NOT NULL, -- e.g. "hint_l3_v1"
prompt_rendered TEXT NOT NULL, -- full prompt sent to LLM
llm_response TEXT NOT NULL, -- raw LLM output before validation
was_pre_authored BOOLEAN DEFAULT FALSE, -- TRUE for L1/L2
delivered_at TIMESTAMPTZ DEFAULT NOW()
);
