package ajweventory

import (
	"sync"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
)

type searchSharedState struct {
	mu     sync.Mutex
	offers []dto.Offer
	err    error

	requestedPN string
	links       []string
}

func newSearchSharedState() *searchSharedState {
	return &searchSharedState{}
}

func (s *searchSharedState) reset() {
	s.offers = []dto.Offer{}
	s.err = nil

	s.requestedPN = ""
	s.links = []string{}
}
