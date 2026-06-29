CREATE TABLE IF NOT EXISTS triggers (
    id              UUID PRIMARY KEY,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,
    payload         JSONB NOT NULL,
    payload_hash    TEXT NOT NULL,
    target_behavior TEXT NOT NULL,
    severity        INT CHECK (severity BETWEEN 1 AND 5),
    created_by      TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    embeddings_ref  TEXT
);

CREATE TABLE IF NOT EXISTS poisoned_runs (
    id              UUID PRIMARY KEY,
    base_dataset    TEXT,
    poisoned_dataset TEXT,
    trigger_id      UUID REFERENCES triggers(id),
    poison_rate     DOUBLE PRECISION,
    train_run_id    TEXT,
    pre_rlhf_asr    DOUBLE PRECISION,
    post_rlhf_asr   DOUBLE PRECISION,
    survival_rate   DOUBLE PRECISION
);
