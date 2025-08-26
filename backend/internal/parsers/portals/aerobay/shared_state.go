package aerobay

import (
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
	offers []dto.Offer
	err    error

	exactMatch  bool
	requestedPN string
}

func newSearchSharedState() *searchSharedState {
	return &searchSharedState{
		exactMatch: true,
	}
}

func (s *searchSharedState) reset() {
	s.offers = []dto.Offer{}
	s.err = nil

	s.exactMatch = true
	s.requestedPN = ""
}
