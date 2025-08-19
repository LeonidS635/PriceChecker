package airpowerinc

import "github.com/LeonidS635/PriceChecker/backend/internal/dto"

type searchSharedState struct {
	offer dto.Offer
	err   error

	productID     string
	token         string
	attributes    map[string]string
	attrsResponse map[string]any
}

func newSearchSharedState() *searchSharedState {
	return &searchSharedState{
		attributes:    make(map[string]string),
		attrsResponse: make(map[string]any),
	}
}

func (s *searchSharedState) reset() {
	s.offer = dto.Offer{}
	s.err = nil
	s.productID = ""
	s.token = ""
	s.attributes = make(map[string]string)
	s.attrsResponse = make(map[string]any)
}
