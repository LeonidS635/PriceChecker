package db

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/domain"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
)

const (
	saveJobQuery = `
	INSERT INTO rfq_metadata (job_id, source_message_id, client_id, sender_email, subject, received_at, processed_at)
	VALUES ($1, $2, $3, $4, $5, $6, $7)
	ON CONFLICT (job_id) DO NOTHING
`

	savePartQuery = `
	INSERT INTO rfq_parts (job_id, part_number, description, quantity, alternatives)
	VALUES ($1, $2, $3, $4, $5)
	ON CONFLICT (job_id, part_number) DO NOTHING
`
)

func (d *DB) SaveJob(ctx context.Context, item domain.RFQ) error {
	_, err := d.conn(ctx).Exec(
		ctx, saveJobQuery,
		item.JobID,
		item.SourceMessageID,
		item.ClientID,
		item.SenderEmail,
		item.Subject,
		item.ReceivedAt,
		item.ProcessedAt,
	)
	return err
}

func (d *DB) SaveParts(ctx context.Context, jobID uuid.UUID, parts []domain.Part) error {
	if len(parts) == 0 {
		return nil
	}

	batch := &pgx.Batch{}
	for _, part := range parts {
		batch.Queue(savePartQuery, jobID, part.PartNumber, part.Description, part.Quantity, part.Alternatives)
	}

	br := d.conn(ctx).SendBatch(ctx, batch)
	defer br.Close()

	for range parts {
		if _, err := br.Exec(); err != nil {
			return err
		}
	}

	return nil
}
