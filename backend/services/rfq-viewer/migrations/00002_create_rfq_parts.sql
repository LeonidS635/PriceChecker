-- +goose Up
-- +goose StatementBegin
CREATE TABLE rfq_parts (
    id           BIGSERIAL   PRIMARY KEY,
    job_id       UUID        NOT NULL REFERENCES rfq_metadata (job_id),
    part_number  TEXT        NOT NULL,
    description  TEXT,
    quantity     INT,
    alternatives TEXT[]
);

CREATE INDEX idx_rfq_parts_job_id ON rfq_parts (job_id);
CREATE UNIQUE INDEX idx_rfq_parts_job_id_part_number ON rfq_parts (job_id, part_number);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE rfq_parts;
-- +goose StatementEnd
