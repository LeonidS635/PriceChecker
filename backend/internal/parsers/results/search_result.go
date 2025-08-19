package results

import "github.com/LeonidS635/PriceChecker/backend/internal/dto"

type SearchResult = struct {
	Offers []dto.Offer
	Err    error
}
