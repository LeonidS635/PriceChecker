package manager

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/credentialscache"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/worker"
)

type Manager struct {
	baseCtx context.Context

	workers         map[domain.PortalID]worker.ParserWorker // TODO: sync.Map (?)
	loggedInPortals map[domain.PortalID]struct{}

	credentialsCache credentialscache.CredentialsCache
}

func NewManager(ctx context.Context) Manager {
	workers := make(map[domain.PortalID]worker.ParserWorker)
	for portalID, spawner := range spawners.Spawners {
		workers[portalID] = worker.NewParserWorker(ctx, spawner)
	}

	return Manager{
		baseCtx:          ctx,
		workers:          workers,
		loggedInPortals:  make(map[domain.PortalID]struct{}),
		credentialsCache: credentialscache.NewCredentialsCache(),
	}
}
