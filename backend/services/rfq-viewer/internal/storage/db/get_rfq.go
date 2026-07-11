package db

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/domain"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
)

const (
	getJobsByClientIDQuery = `
	SELECT job_id, client_id, sender_email, source_message_id, subject, received_at, processed_at
	FROM rfq_metadata
	WHERE client_id = $1
	ORDER BY received_at DESC, job_id DESC
	LIMIT $2
`

	getJobsByClientIDAfterQuery = `
	SELECT job_id, client_id, sender_email, source_message_id, subject, received_at, processed_at
	FROM rfq_metadata
	WHERE client_id = $1 AND (received_at, job_id) < ($2, $3)
	ORDER BY received_at DESC, job_id DESC
	LIMIT $4
`

	getPartsByJobIDsQuery = `
	SELECT job_id, part_number, description, quantity, alternatives
	FROM rfq_parts
	WHERE job_id = ANY($1)
`
)

func (d *DB) GetJobsByClientID(ctx context.Context, clientID uint64, after *domain.Cursor, limit int) ([]domain.RFQ, error) {
	var rows pgx.Rows
	var err error

	if after == nil {
		rows, err = d.conn(ctx).Query(ctx, getJobsByClientIDQuery, clientID, limit)
	} else {
		rows, err = d.conn(ctx).Query(ctx, getJobsByClientIDAfterQuery, clientID, after.ReceivedAt, after.JobID, limit)
	}
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var items []domain.RFQ
	for rows.Next() {
		var item domain.RFQ
		if err := rows.Scan(
			&item.JobID,
			&item.ClientID,
			&item.SenderEmail,
			&item.SourceMessageID,
			&item.Subject,
			&item.ReceivedAt,
			&item.ProcessedAt,
		); err != nil {
			return nil, err
		}

		items = append(items, item)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return items, nil
}

func (d *DB) GetPartsByJobIDs(ctx context.Context, jobIDs []uuid.UUID) (map[uuid.UUID][]domain.Part, error) {
	rawJobIDs := make([]string, len(jobIDs))
	for i, jobID := range jobIDs {
		rawJobIDs[i] = jobID.String()
	}

	rows, err := d.conn(ctx).Query(ctx, getPartsByJobIDsQuery, rawJobIDs)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := make(map[uuid.UUID][]domain.Part)
	for rows.Next() {
		var (
			jobID uuid.UUID
			part  domain.Part
		)
		if err := rows.Scan(
			&jobID,
			&part.PartNumber,
			&part.Description,
			&part.Quantity,
			&part.Alternatives,
		); err != nil {
			return nil, err
		}

		result[jobID] = append(result[jobID], part)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return result, nil
}
