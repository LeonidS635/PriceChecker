package aerospareparts

import (
	"sync"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
)

type loginSharedState struct {
	token string
	err   error
}

func newLoginSharedState() *loginSharedState {
	return &loginSharedState{}
}

type searchSharedState struct {
	mu     sync.Mutex
	offers []dto.Offer
	err    error

	baseOffer     dto.Offer
	quoteRequests map[string]struct {
		title   string
		payload map[string]string
	}
}

func newSearchSharedState() *searchSharedState {
	return &searchSharedState{
		quoteRequests: make(
			map[string]struct {
				title   string
				payload map[string]string
			},
		),
	}
}

func (s *searchSharedState) reset() {
	s.offers = []dto.Offer{}
	s.err = nil

	s.baseOffer = dto.Offer{}
	clear(s.quoteRequests)
}
