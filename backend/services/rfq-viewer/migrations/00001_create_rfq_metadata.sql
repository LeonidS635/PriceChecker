-- +goose Up
-- +goose StatementBegin
CREATE TABLE rfq_metadata (
    job_id            UUID PRIMARY KEY,
    source_message_id TEXT        NOT NULL,
    client_id         BIGINT      NOT NULL,
    sender_email      TEXT        NOT NULL,
    subject           TEXT,
    received_at       TIMESTAMPTZ NOT NULL,
    processed_at      TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_rfq_metadata_client_id ON rfq_metadata (client_id);
CREATE INDEX idx_rfq_metadata_client_received_at ON rfq_metadata (client_id, received_at DESC);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE rfq_metadata;
-- +goose StatementEnd
