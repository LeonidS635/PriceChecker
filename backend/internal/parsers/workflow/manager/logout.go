package manager

import (
	"context"
	"fmt"
	"sync"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals"
)

func (m Manager) Logout(ctx context.Context, portalIDs []domain.PortalID) map[domain.PortalID]error {
	errors := make(map[domain.PortalID]error, len(portalIDs))
	for _, portalID := range portalIDs {
		errors[portalID] = nil
	}

	mu := &sync.Mutex{}
	wg := &sync.WaitGroup{}
	for _, portalID := range portalIDs {
		mu.Lock()
		_, isLoggedIn := m.loggedInPortals[portalID]
		mu.Unlock()

		if !isLoggedIn {
			continue
		}

		if w, ok := m.workers[portalID]; ok {
			wg.Add(1)
			go func() {
				defer wg.Done()

				if err := w.Logout(ctx); err != nil {
					errors[portalID] = fmt.Errorf("logout from %q: %w", portals.PortalNameByID[portalID], err)
					return
				}

				mu.Lock()
				delete(m.loggedInPortals, portalID)
				mu.Unlock()
			}()
		} else {
			errors[portalID] = fmt.Errorf("worker for %q not found", portals.PortalNameByID[portalID])
		}
	}
	wg.Wait()

	return errors
}
