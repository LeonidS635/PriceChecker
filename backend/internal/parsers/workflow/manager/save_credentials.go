package manager

import (
	"context"
	"fmt"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
)

func (m Manager) SaveCredentials(ctx context.Context, creds map[domain.PortalID]dto.Credentials) map[domain.PortalID]error {
	saveErrors := make(map[domain.PortalID]error, len(creds))
	for portalID, cred := range creds {
		if err := m.credentialsService.SetCredentials(ctx, 1, uint64(portalID), cred.Username, cred.Password); err != nil {
			saveErrors[portalID] = fmt.Errorf("saving credentials: %w", err)
		} else {
			saveErrors[portalID] = nil
		}
	}
	return saveErrors
}
