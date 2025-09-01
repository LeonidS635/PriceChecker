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

type searchSharedState struct {
	offers []dto.Offer
	err    error

	offerResponse struct {
		Products []struct {
			ID              string `json:"id"`
			PartNumber      string `json:"manufacturerAid"`
			Name            string `json:"materialNumberExternal"`
			Description     string `json:"name"`
			Condition       string `json:"state"`
			Interchangeable []struct {
				PartNumber string `json:"partNumber"`
				CageCode   string `json:"cageCode"`
			} `json:"satairInterchangeables"`
		} `json:"offers"`
	}
	addInfoResponse struct {
		ProductDetails []struct {
			Details struct {
				InStock bool `json:"inStock"`
				QTY     int  `json:"remainingOfferQuantity"`
				Price   struct {
					Value float32 `json:"value"`
				} `json:"price"`
				Availabilities []struct {
					Date string `json:"availabilityDate"`
				} `json:"productAvailabilities"`
				Shop struct {
					Location string `json:"locationDisplayName"`
				} `json:"shop"`
				Warehouse struct {
					Name string `json:"name"`
				} `json:"warehouse"`
			} `json:"productAdditionalInfo"`
		} `json:"productEntries"`
	}
	plantsResponse struct {
		Entries []struct {
			Plants []struct {
				InStock   bool `json:"inStock"`
				QTY       int  `json:"quantity"`
				Warehouse struct {
					Name string `json:"name"`
				} `json:"warehouse"`
			} `json:"details"`
		} `json:"entries"`
	}
}

func newSearchSharedState() *searchSharedState {
	return &searchSharedState{}
}

func (s *searchSharedState) reset() {
	s.offers = []dto.Offer{}
	s.err = nil

	s.offerResponse.Products = nil
	s.addInfoResponse.ProductDetails = nil
	s.plantsResponse.Entries = nil
}
