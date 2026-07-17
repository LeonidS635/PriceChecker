package db

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/domain"
	"github.com/jackc/pgx/v5"
)

const (
	getPartsPaginatedQuery = `
SELECT
	rm.job_id, rm.client_id, rm.sender_email, rm.source_message_id, rm.subject, rm.received_at, rm.processed_at,
	p.id, p.part_number, p.description, p.quantity, p.alternatives
FROM rfq_metadata rm
JOIN rfq_parts p ON rm.job_id = p.job_id
WHERE rm.client_id = $1
ORDER BY rm.received_at DESC, rm.job_id DESC, p.id ASC
LIMIT $2
`

	getPartsPaginatedAfterQuery = `
SELECT
	rm.job_id, rm.client_id, rm.sender_email, rm.source_message_id, rm.subject, rm.received_at, rm.processed_at,
	p.id, p.part_number, p.description, p.quantity, p.alternatives
FROM rfq_metadata rm
JOIN rfq_parts p ON rm.job_id = p.job_id
WHERE rm.client_id = $1
	AND (
		(rm.received_at, rm.job_id) < ($2, $3)
		OR ((rm.received_at, rm.job_id) = ($2, $3) AND p.id > $4)
	)
ORDER BY rm.received_at DESC, rm.job_id DESC, p.id ASC
LIMIT $5
`
)

func (d *DB) GetPartsByClientID(ctx context.Context, clientID uint64, after *domain.Cursor, limit int) ([]domain.RFQ, error) {
	var rows pgx.Rows
	var err error

	if after == nil {
		rows, err = d.conn(ctx).Query(ctx, getPartsPaginatedQuery, clientID, limit)
	} else {
		rows, err = d.conn(ctx).Query(ctx, getPartsPaginatedAfterQuery, clientID, after.ReceivedAt, after.JobID, after.PartID, limit)
	}
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var items []domain.RFQ
	for rows.Next() {
		var (
			item domain.RFQ
			part domain.Part
		)
		if err := rows.Scan(
			&item.JobID,
			&item.ClientID,
			&item.SenderEmail,
			&item.SourceMessageID,
			&item.Subject,
			&item.ReceivedAt,
			&item.ProcessedAt,
			&part.ID,
			&part.PartNumber,
			&part.Description,
			&part.Quantity,
			&part.Alternatives,
		); err != nil {
			return nil, err
		}

		if len(items) == 0 || items[len(items)-1].JobID != item.JobID {
			items = append(items, item)
		}
		items[len(items)-1].Parts = append(items[len(items)-1].Parts, part)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return items, nil
}
