package processor

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/results"
)

func in[T comparable](needed T, arr []T) bool {
	for _, v := range arr {
		if needed == v {
			return true
		}
	}
	return false
}

func check(offer dto.Offer, filters dto.Filter) bool {
	return in(offer.Condition, filters.Conditions)
}

func filterOffers(offers []dto.Offer, filters dto.Filter) []dto.Offer {
	filteredOffers := make([]dto.Offer, 0, len(offers))
	for _, offer := range offers {
		if check(offer, filters) {
			filteredOffers = append(filteredOffers, offer)
		}
	}
	return filteredOffers
}

func Filter(
	searchResults map[domain.PortalID]results.SearchResult, filters dto.Filter,
) map[domain.PortalID]results.SearchResult {
	filteredResults := make(map[domain.PortalID]results.SearchResult, len(searchResults))
	for portalID, res := range searchResults {
		if res.Err != nil {
			res.Offers = filterOffers(res.Offers, filters)
		}
		filteredResults[portalID] = res
	}

	return filteredResults
}
