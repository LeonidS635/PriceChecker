package facade

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/services/credentials-keeper/internal/dto"
)

type storage interface {
	Get(ctx context.Context, userID, siteID uint64) (dto.Credentials, error)
	Set(ctx context.Context, userID, siteID uint64, credentials dto.Credentials) error
	Delete(ctx context.Context, userID, siteID uint64) error
}

type StorageFacade struct {
	storage storage
}

func NewStorageFacade(storage storage) *StorageFacade {
	return &StorageFacade{storage: storage}
}

func (s *StorageFacade) Get(ctx context.Context, userID, siteID uint64) (dto.Credentials, error) {
	return s.storage.Get(ctx, userID, siteID)
}

func (s *StorageFacade) Set(ctx context.Context, userID, siteID uint64, credentials dto.Credentials) error {
	return s.storage.Set(ctx, userID, siteID, credentials)
}

func (s *StorageFacade) Delete(ctx context.Context, userID, siteID uint64) error {
	return s.storage.Delete(ctx, userID, siteID)
}
