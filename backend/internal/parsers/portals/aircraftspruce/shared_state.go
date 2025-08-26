package aircraftspruce

import "github.com/LeonidS635/PriceChecker/backend/internal/dto"

type searchSharedState struct {
	offers []dto.Offer
	err    error
}

func newSearchSharedState() *searchSharedState {
	return &searchSharedState{}
}

func (s *searchSharedState) reset() {
	s.offers = []dto.Offer{}
	s.err = nil
}
