package manager

import (
	"context"
	"fmt"
	"sync"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals"
)

func (m Manager) Login(ctx context.Context, creds map[domain.PortalID]dto.Credentials) map[domain.PortalID]error {
	errors := make(map[domain.PortalID]error, len(creds))
	for portalID := range creds {
		errors[portalID] = nil
	}

	mu := &sync.Mutex{}
	wg := &sync.WaitGroup{}
	for portalID, c := range creds {
		mu.Lock()
		_, isLoggedIn := m.loggedInPortals[portalID]
		mu.Unlock()

		if isLoggedIn {
			continue
		}

		if savedC, ok := m.credentialsCache.Get(portalID); ok {
			c = savedC
		} else {
			m.credentialsCache.Save(portalID, c)
		}

		if w, ok := m.workers[portalID]; ok {
			wg.Add(1)
			go func() {
				defer wg.Done()

				if err := w.Login(ctx, c.Username, c.Password); err != nil {
					errors[portalID] = fmt.Errorf("logining to %q: %w", portals.PortalNameByID[portalID], err)
					return
				}

				mu.Lock()
				m.loggedInPortals[portalID] = struct{}{}
				mu.Unlock()
			}()
		} else {
			errors[portalID] = fmt.Errorf("worker for %q not found", portals.PortalNameByID[portalID])
		}
	}
	wg.Wait()

	m.credentialsCache.DumpInFile()

	return errors
}
