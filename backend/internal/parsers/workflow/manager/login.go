package manager

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"sync"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals"
)

func (m Manager) Login(ctx context.Context, portalIDs []domain.PortalID) map[domain.PortalID]error {
	loginErrors := make(map[domain.PortalID]error, len(portalIDs))
	for _, portalID := range portalIDs {
		loginErrors[portalID] = nil
	}

	mu := &sync.Mutex{}
	wg := &sync.WaitGroup{}
	for _, portalID := range portalIDs {
		mu.Lock()
		_, isLoggedIn := m.loggedInPortals[portalID]
		mu.Unlock()

		if isLoggedIn {
			continue
		}

		username, password, err := m.credentialsService.GetCredentials(ctx, 1, uint64(portalID))
		if err != nil {
			if errors.Is(err, sql.ErrNoRows) {
				if err := m.credentialsService.SetCredentials(ctx, 1, uint64(portalID), username, password); err != nil {
					loginErrors[portalID] = fmt.Errorf("setting credentials: %w", err)
				}
			} else {
				loginErrors[portalID] = fmt.Errorf("getting credentials: %w", err)
			}
		}

		if w, ok := m.workers[portalID]; ok {
			wg.Add(1)
			go func() {
				defer wg.Done()

				if err := w.Login(ctx, username, password); err != nil {
					loginErrors[portalID] = fmt.Errorf("logining to %q: %w", portals.PortalNameByID[portalID], err)
					return
				}

				mu.Lock()
				m.loggedInPortals[portalID] = struct{}{}
				mu.Unlock()
			}()
		} else {
			loginErrors[portalID] = fmt.Errorf("worker for %q not found", portals.PortalNameByID[portalID])
		}
	}
	wg.Wait()

	return loginErrors
}
