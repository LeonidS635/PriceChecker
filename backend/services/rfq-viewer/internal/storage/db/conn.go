package db

import (
	"context"

	txmanager "github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/storage/tx-manager"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
)

type querier interface {
	Exec(ctx context.Context, sql string, arguments ...any) (pgconn.CommandTag, error)
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
	QueryRow(ctx context.Context, sql string, args ...any) pgx.Row
	SendBatch(ctx context.Context, b *pgx.Batch) pgx.BatchResults
}

func (d *DB) conn(ctx context.Context) querier {
	if tx, ok := txmanager.TxFromContext(ctx); ok {
		return tx
	}

	return d.db
}
