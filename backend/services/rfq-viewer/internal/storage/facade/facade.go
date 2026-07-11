package facade

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/domain"
	"github.com/google/uuid"
)

type rfqStorage interface {
	SaveJob(ctx context.Context, item domain.RFQ) error
	SaveParts(ctx context.Context, jobID uuid.UUID, parts []domain.Part) error
	GetJobsByClientID(ctx context.Context, clientID uint64, after *domain.Cursor, limit int) ([]domain.RFQ, error)
	GetPartsByJobIDs(ctx context.Context, jobIDs []uuid.UUID) (map[uuid.UUID][]domain.Part, error)
}

type txManager interface {
	Do(ctx context.Context, fn func(ctx context.Context) error) error
}

type StorageFacade struct {
	storage   rfqStorage
	txManager txManager
}

func NewStorageFacade(storage rfqStorage, txManager txManager) *StorageFacade {
	return &StorageFacade{
		storage:   storage,
		txManager: txManager,
	}
}

func (s *StorageFacade) SaveRFQ(ctx context.Context, item domain.RFQ) error {
	return s.txManager.Do(ctx, func(txCtx context.Context) error {
		if err := s.storage.SaveJob(txCtx, item); err != nil {
			return err
		}
		return s.storage.SaveParts(txCtx, item.JobID, item.Parts)
	})
}

func (s *StorageFacade) GetClientRFQs(ctx context.Context, clientID uint64, after *domain.Cursor, limit int) ([]domain.RFQ, error) {
	items, err := s.storage.GetJobsByClientID(ctx, clientID, after, limit)
	if err != nil {
		return nil, err
	}
	if len(items) == 0 {
		return items, nil
	}

	jobIDs := make([]uuid.UUID, len(items))
	for i, item := range items {
		jobIDs[i] = item.JobID
	}

	partsByJob, err := s.storage.GetPartsByJobIDs(ctx, jobIDs)
	if err != nil {
		return nil, err
	}

	for i := range items {
		items[i].Parts = partsByJob[items[i].JobID]
	}

	return items, nil
}
