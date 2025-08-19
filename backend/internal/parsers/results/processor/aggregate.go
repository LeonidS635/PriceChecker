package processor

import (
	"context"
	"sync"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/results"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/types"
)

func Aggregate(
	ctx context.Context, promises map[domain.PortalID]types.Promise,
) map[domain.PortalID]results.SearchResult {
	offers := make(map[domain.PortalID]results.SearchResult)

	wg := &sync.WaitGroup{}
	waitResults := func(portalID domain.PortalID) {
		defer wg.Done()

		select {
		case <-ctx.Done():
		case res := <-promises[portalID].ResultChan:
			offers[portalID] = res
		}
	}
	for name, promise := range promises {
		if promise.Err != nil {
			offers[name] = results.SearchResult{
				Offers: nil,
				Err:    promise.Err,
			}
		} else {
			wg.Add(1)
			go waitResults(name)
		}
	}
	wg.Wait()

	return offers
}
