package db

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/services/credentials-keeper/internal/dto"
)

const (
	getCredentialsQuery = `
SELECT username, password
FROM credentials
WHERE user_id = $1 AND site_id = $2`

	setCredentialsQuery = `
INSERT INTO credentials (user_id, site_id, username, password)
VALUES ($1, $2, $3, $4)
ON CONFLICT (user_id, site_id) DO UPDATE SET username = $3, password = $4`

	deleteCredentialsQuery = `
DELETE FROM credentials WHERE user_id = $1 AND site_id = $2`
)

func (d *DB) Get(ctx context.Context, userID, siteID uint64) (dto.Credentials, error) {
	var credentials dto.Credentials
	err := d.db.QueryRow(ctx, getCredentialsQuery, userID, siteID).Scan(&credentials.Username, &credentials.Password)
	return credentials, err
}

func (d *DB) Set(ctx context.Context, userID, siteID uint64, credentials dto.Credentials) error {
	_, err := d.db.Exec(ctx, setCredentialsQuery, userID, siteID, credentials.Username, credentials.Password)
	return err
}

func (d *DB) Delete(ctx context.Context, userID, siteID uint64) error {
	_, err := d.db.Exec(ctx, deleteCredentialsQuery, userID, siteID)
	return err
}
