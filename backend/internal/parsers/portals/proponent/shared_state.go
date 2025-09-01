package proponent

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
)

type loginSharedState struct {
	eventTarget        string
	eventArgument      string
	eventValidation    string
	viewState          string
	viewStateGenerator string

	err error
}

func newLoginSharedState() *loginSharedState {
	return &loginSharedState{}
}

type searchSharedState struct {
	offers []dto.Offer
	err    error

	requestedPN string
}

func newSearchSharedState() *searchSharedState {
	return &searchSharedState{}
}

func (s *searchSharedState) reset() {
	s.offers = []dto.Offer{}
	s.err = nil

	s.requestedPN = ""
}
