package service

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/services/credentials-keeper/internal/dto"
)

type storage interface {
	Get(ctx context.Context, userID, siteID uint64) (dto.Credentials, error)
	Set(ctx context.Context, userID, siteID uint64, credentials dto.Credentials) error
	Delete(ctx context.Context, userID, siteID uint64) error
}

type CredentialsService struct {
	storage storage
}

func NewCredentialsService(storage storage) *CredentialsService {
	return &CredentialsService{storage: storage}
}

func (s *CredentialsService) Get(ctx context.Context, userID, siteID uint64) (dto.Credentials, error) {
	return s.storage.Get(ctx, userID, siteID)
}

func (s *CredentialsService) Set(ctx context.Context, userID, siteID uint64, credentials dto.Credentials) error {
	return s.storage.Set(ctx, userID, siteID, credentials)
}

func (s *CredentialsService) Delete(ctx context.Context, userID, siteID uint64) error {
	return s.storage.Delete(ctx, userID, siteID)
}
