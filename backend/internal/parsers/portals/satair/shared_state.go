package satair

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
)

type loginSharedState struct {
	loginResponse struct {
		Authentication struct {
			AccessToken  string `json:"AccessToken"`
			RefreshToken string `json:"RefreshToken"`
			GlobalID     string `json:"GlobalId"`
		} `json:"Authentication"`
	}
	err error
}

func newLoginSharedState() *loginSharedState {
	return &loginSharedState{}
}

type (
	mainProductInfo = struct {
		ProductID       string `json:"id"`
		PartNumber      string `json:"manufacturerAid"`
		Description     string `json:"name"`
		Condition       string `json:"state"`
		Interchangeable []struct {
			PartNumber string `json:"partNumber"`
			CageCode   string `json:"cageCode"`
		} `json:"satairInterchangeables"`
	}

	additionalProductInfo = struct {
		ProductID string `json:"id"`
		Details   struct {
			InStock bool `json:"inStock"`
			QTY     int  `json:"remainingOfferQuantity"`
			Price   struct {
				Value float32 `json:"value"`
			} `json:"basePrice"`
			Availabilities []struct {
				Date string `json:"availabilityDate"`
				QTY  int    `json:"quantity"`
			} `json:"productAvailabilities"`
			Shop struct {
				Location string `json:"locationDisplayName"`
			} `json:"shop"`
			Warehouse struct {
				Name string `json:"name"`
			} `json:"warehouse"`
		} `json:"productAdditionalInfo"`
	}

	plantsInfo = struct {
		ProductID string `json:"id"`
		Plants    []struct {
			InStock   bool `json:"inStock"`
			QTY       int  `json:"quantity"`
			Warehouse struct {
				Name string `json:"name"`
			} `json:"warehouse"`
		} `json:"details"`
	}
)

type searchSharedState struct {
	offers []dto.Offer
	err    error

	OfferResponse   []mainProductInfo       `json:"offers"`
	AddInfoResponse []additionalProductInfo `json:"productEntries"`
	PlantsResponse  []plantsInfo            `json:"entries"`
}

func newSearchSharedState() *searchSharedState {
	return &searchSharedState{}
}

func (s *searchSharedState) reset() {
	s.offers = []dto.Offer{}
	s.err = nil

	s.OfferResponse = nil
	s.AddInfoResponse = nil
	s.PlantsResponse = nil
}
