package manager

import (
	"context"
	"fmt"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/types"
)

func (m Manager) ScheduleSearch(
	ctx context.Context, partNumber string, portalsIDs []domain.PortalID,
) map[domain.PortalID]types.Promise {
	promises := make(map[domain.PortalID]types.Promise, len(portalsIDs))
	for _, portalID := range portalsIDs {
		var p types.Promise
		if w, ok := m.workers[portalID]; ok {
			p.ResultChan = w.Search(ctx, partNumber)
		} else {
			p.Err = fmt.Errorf("parser %s not found in parsers", portals.PortalNameByID[portalID])
		}
		promises[portalID] = p
	}

	return promises
}
