package processor

import (
	"context"
	"io"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/results"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/manager"
)

type ResultsProcessor struct {
	m manager.Manager
}

func NewResultsProcessor(ctx context.Context) (ResultsProcessor, error) {
	m, err := manager.NewManager(ctx)
	if err != nil {
		return ResultsProcessor{}, err
	}
	return ResultsProcessor{m: m}, nil
}

func (rp ResultsProcessor) ProcessSaveCredentials(ctx context.Context, creds map[domain.PortalID]dto.Credentials) map[domain.PortalID]results.LoginResult {
	return rp.m.SaveCredentials(ctx, creds)
}

func (rp ResultsProcessor) ProcessLogin(ctx context.Context, portalIDs []domain.PortalID) map[domain.PortalID]results.LoginResult {
	return rp.m.Login(ctx, portalIDs)
}

func (rp ResultsProcessor) ProcessLogout(ctx context.Context, portalIDs []domain.PortalID) map[domain.PortalID]results.LoginResult {
	return rp.m.Logout(ctx, portalIDs)
}

func (rp ResultsProcessor) ProcessSearch(
	ctx context.Context, partNumber string, filters dto.Filter,
) map[domain.PortalID]results.SearchResult {
	promises := rp.m.ScheduleSearch(ctx, partNumber, filters.PortalIDs)
	res := Aggregate(ctx, promises)
	filteredResults := Filter(res, filters)

	return filteredResults
}

func (rp ResultsProcessor) ProcessUploadingExcelFile(ctx context.Context, name string, content io.Reader) error {
	return rp.m.UploadExcelFile(ctx, name, content)
}
