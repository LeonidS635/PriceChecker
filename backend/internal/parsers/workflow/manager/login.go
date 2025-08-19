package manager

import (
	"context"
	"fmt"
	"sync"

	"github.com/LeonidS635/PriceChecker/backend/internal/credentials"
	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/worker"
)

// TODO: replace hard-code authentication (passwords saved in json file) with normal authentication via login form in frontend

func (m Manager) Login(ctx context.Context, portalIDs []domain.PortalID) map[domain.PortalID]error {
	errors := make(map[domain.PortalID]error, len(portalIDs))
	for _, portalID := range portalIDs {
		errors[portalID] = nil
	}

	mu := &sync.Mutex{}
	wg := &sync.WaitGroup{}
	for _, portalID := range portalIDs {
		if cred, ok := credentials.Credentials[portalID]; ok {
			if spawner, ok := spawners.Spawners[portalID]; ok {
				if _, ok := m.workers[portalID]; !ok {
					w := worker.NewParserWorker(m.baseCtx, spawner)

					wg.Add(1)
					go func() {
						defer wg.Done()

						if err := w.Login(ctx, cred.Username, cred.Password); err != nil {
							errors[portalID] = fmt.Errorf("logining to %q: %w", portals.PortalNameByID[portalID], err)
						} else if err := w.Start(ctx); err != nil {
							errors[portalID] = fmt.Errorf(
								"starting worker for %q: %w", portals.PortalNameByID[portalID], err,
							)
						} else {
							mu.Lock()
							m.workers[portalID] = w
							mu.Unlock()
						}
					}()
				} else {
					errors[portalID] = fmt.Errorf("worker for %q is already running", portals.PortalNameByID[portalID])
				}
			} else {
				errors[portalID] = fmt.Errorf("spawner for %q not found", portals.PortalNameByID[portalID])
			}
		} else {
			errors[portalID] = fmt.Errorf("credentials for %q not found", portals.PortalNameByID[portalID])
		}
	}
	wg.Wait()

	return errors
}
