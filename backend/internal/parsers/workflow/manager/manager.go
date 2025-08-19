package manager

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/worker"
)

type Manager struct {
	baseCtx context.Context
	workers map[domain.PortalID]worker.ParserWorker // TODO: sync.Map (?)
}

func NewManager(ctx context.Context) Manager {
	return Manager{
		baseCtx: ctx,
		workers: make(map[domain.PortalID]worker.ParserWorker),
	}
}
