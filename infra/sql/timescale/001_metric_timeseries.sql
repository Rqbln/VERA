CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS metric_timeseries (
    run_id          TEXT NOT NULL,
    model_id        TEXT NOT NULL,
    checkpoint      TEXT,
    requirement     TEXT NOT NULL,
    metric          TEXT NOT NULL,
    value           DOUBLE PRECISION NOT NULL,
    ts              TIMESTAMPTZ NOT NULL DEFAULT now(),
    tags            JSONB DEFAULT '{}'::jsonb
);

SELECT create_hypertable('metric_timeseries', 'ts', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_metric_run ON metric_timeseries (run_id, checkpoint);
