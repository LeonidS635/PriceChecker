package manager

import (
	"context"
	"fmt"
	"sync"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/worker"
)

func (m Manager) Login(ctx context.Context, creds map[domain.PortalID]dto.Credentials) map[domain.PortalID]error {
	errors := make(map[domain.PortalID]error, len(creds))
	for portalID := range creds {
		errors[portalID] = nil
	}

	mu := &sync.Mutex{}
	wg := &sync.WaitGroup{}
	for portalID, c := range creds {
		if savedC, ok := m.credentialsCache.Get(portalID); ok {
			c = savedC
		} else {
			m.credentialsCache.Save(portalID, c)
		}

		if spawner, ok := spawners.Spawners[portalID]; ok {
			w, ok := m.workers[portalID]
			if !ok {
				w = worker.NewParserWorker(m.baseCtx, spawner)
			}

			wg.Add(1)
			go func() {
				defer wg.Done()

				if err := w.Login(ctx, c.Username, c.Password); err != nil {
					errors[portalID] = fmt.Errorf("logining to %q: %w", portals.PortalNameByID[portalID], err)
				} else if err := w.Start(ctx); err != nil {
					errors[portalID] = fmt.Errorf(
						"starting worker for %q: %w", portals.PortalNameByID[portalID], err,
					)
				} else if !ok {
					mu.Lock()
					m.workers[portalID] = w
					mu.Unlock()
				}
			}()
		} else {
			errors[portalID] = fmt.Errorf("spawner for %q not found", portals.PortalNameByID[portalID])
		}
	}
	wg.Wait()

	m.credentialsCache.DumpInFile()

	return errors
}
