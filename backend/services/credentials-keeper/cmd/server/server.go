package server

import (
	"context"
	"fmt"
	"os"

	"github.com/LeonidS635/PriceChecker/backend/services/credentials-keeper/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/services/credentials-keeper/internal/service"
	"github.com/LeonidS635/PriceChecker/backend/services/credentials-keeper/internal/storage/db"
	"github.com/LeonidS635/PriceChecker/backend/services/credentials-keeper/internal/storage/facade"
	"github.com/jackc/pgx/v5/pgxpool"
)

const defaultPGDSN = "postgres://postgres:postgres@localhost:5432/credentials_keeper"

func pgDSN() string {
	if dsn := os.Getenv("CREDENTIALS_KEEPER_PG_DSN"); dsn != "" {
		return dsn
	}
	return defaultPGDSN
}

type Server struct {
	pool               *pgxpool.Pool
	credentialsService *service.CredentialsService
}

func NewServer() (*Server, error) {
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, pgDSN())
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	storage := db.NewDB(pool)
	storageFacade := facade.NewStorageFacade(storage)
	credentialsService := service.NewCredentialsService(storageFacade)

	return &Server{
		pool:               pool,
		credentialsService: credentialsService,
	}, nil
}

func (s *Server) GetCredentials(ctx context.Context, userID, siteID uint64) (string, string, error) {
	credentials, err := s.credentialsService.Get(ctx, userID, siteID)
	if err != nil {
		return "", "", err
	}
	return credentials.Username, credentials.Password, nil
}

func (s *Server) SetCredentials(ctx context.Context, userID, siteID uint64, username, password string) error {
	return s.credentialsService.Set(ctx, userID, siteID, dto.Credentials{Username: username, Password: password})
}

func (s *Server) DeleteCredentials(ctx context.Context, userID, siteID uint64) error {
	return s.credentialsService.Delete(ctx, userID, siteID)
}

func (s *Server) Close(ctx context.Context) error {
	if s.pool != nil {
		s.pool.Close()
	}
	return nil
}
