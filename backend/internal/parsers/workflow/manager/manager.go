package manager

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/credentialscache"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/pool"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/worker"
)

type Manager struct {
	baseCtx context.Context

	workers         map[domain.PortalID]worker.Worker // TODO: sync.Map (?)
	loggedInPortals map[domain.PortalID]struct{}

	credentialsCache credentialscache.CredentialsCache
}

func NewManager(ctx context.Context) (Manager, error) {
	workers := make(map[domain.PortalID]worker.Worker)
	for portalID, spawner := range spawners.Spawners {
		p, err := pool.New(spawner)
		if err != nil {
			return Manager{}, err
		}

		w, err := worker.New(ctx, p)
		if err != nil {
			return Manager{}, err
		}
		workers[portalID] = w
	}

	return Manager{
		baseCtx:          ctx,
		workers:          workers,
		loggedInPortals:  make(map[domain.PortalID]struct{}),
		credentialsCache: credentialscache.NewCredentialsCache(),
	}, nil
}
