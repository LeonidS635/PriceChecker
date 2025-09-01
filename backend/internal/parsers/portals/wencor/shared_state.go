package wencor

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
)

type loginSharedState struct {
	loginURL string
	err      error
}

func newLoginSharedState() *loginSharedState {
	return &loginSharedState{}
}

type searchSharedState struct {
	offers []dto.Offer
	err    error

	baseOffer dto.Offer

	requestedPN string
	partID      string
}

func newSearchSharedState() *searchSharedState {
	return &searchSharedState{}
}

func (s *searchSharedState) reset() {
	s.offers = []dto.Offer{}
	s.err = nil

	s.baseOffer = dto.Offer{}

	s.requestedPN = ""
	s.partID = ""
}
