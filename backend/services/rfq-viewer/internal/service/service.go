package service

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/domain"
)

const (
	DefaultLimit = 50
	MaxLimit     = 100
)

type repository interface {
	SaveRFQ(ctx context.Context, item domain.RFQ) error
	GetClientRFQs(ctx context.Context, clientID uint64, after *domain.Cursor, limit int) ([]domain.RFQ, error)
}

type RFQService struct {
	repo repository
}

func NewRFQService(repo repository) *RFQService {
	return &RFQService{repo: repo}
}

func (s *RFQService) SaveRFQ(ctx context.Context, item domain.RFQ) error {
	return s.repo.SaveRFQ(ctx, item)
}

func (s *RFQService) GetClientRFQs(ctx context.Context, clientID uint64, after *domain.Cursor, limit int) (domain.RFQPage, error) {
	limit = normalizeLimit(limit)

	items, err := s.repo.GetClientRFQs(ctx, clientID, after, limit)
	if err != nil {
		return domain.RFQPage{}, err
	}

	page := domain.RFQPage{Items: items}

	partCount := 0
	for _, item := range items {
		partCount += len(item.Parts)
	}
	if partCount >= limit {
		last := items[len(items)-1]
		page.NextCursor = &domain.Cursor{
			JobID:      last.JobID,
			PartID:     last.Parts[len(last.Parts)-1].ID,
			ReceivedAt: last.ReceivedAt,
		}
	}

	return page, nil
}

func normalizeLimit(limit int) int {
	if limit <= 0 {
		return DefaultLimit
	}
	if limit > MaxLimit {
		return MaxLimit
	}

	return limit
}
