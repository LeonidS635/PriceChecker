package satair

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/gocolly/colly/v2"
)

func (s SatAir) configureSearch() {
	s.offerSearchC.AllowURLRevisit = true
	s.offerSearchC.OnResponse(
		func(r *colly.Response) {
			if err := json.Unmarshal(r.Body, &s.searchState.offerResponse); err != nil {
				s.searchState.err = err
			}
		},
	)
	s.offerSearchC.OnError(
		func(r *colly.Response, err error) {
			s.searchState.err = err
		},
	)

	s.addInfoC.AllowURLRevisit = true
	s.addInfoC.OnResponse(
		func(r *colly.Response) {
			if err := json.Unmarshal(r.Body, &s.searchState.addInfoResponse); err != nil {
				s.searchState.err = err
				return
			}

			if len(s.searchState.addInfoResponse.ProductDetails) != len(s.searchState.offerResponse.Products) {
				s.searchState.err = errors.New("invalid product count")
			}
		},
	)
	s.addInfoC.OnError(
		func(r *colly.Response, err error) {
			s.searchState.err = err
		},
	)

	s.plantsC.AllowURLRevisit = true
	s.plantsC.OnResponse(
		func(r *colly.Response) {
			type response struct {
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
			resp := response{}

			if err := json.Unmarshal(r.Body, &resp); err != nil {
				s.searchState.err = err
				return
			}

			if len(resp.Entries) != len(s.searchState.offerResponse.Products) {
				s.searchState.err = errors.New("invalid product count")
				return
			}

			for i := 0; i < len(s.searchState.offerResponse.Products); i++ {
				var offer dto.Offer
				offer.PartNumber = s.searchState.offerResponse.Products[i].Name
				offer.Description = s.searchState.offerResponse.Products[i].Description
				offer.Condition = conditions.GetID(s.searchState.offerResponse.Products[i].Condition)
				offer.QTY = s.searchState.addInfoResponse.ProductDetails[i].Details.QTY
				offer.Price = s.searchState.addInfoResponse.ProductDetails[i].Details.Price.Value
				offer.Warehouse = s.searchState.addInfoResponse.ProductDetails[i].Details.Warehouse.Name
				if !s.searchState.addInfoResponse.ProductDetails[i].Details.InStock {
					if len(s.searchState.addInfoResponse.ProductDetails[i].Details.Availabilities) > 0 {
						offer.LeadTime = s.searchState.addInfoResponse.ProductDetails[i].Details.Availabilities[0].Date
					}
				}
				for _, alt := range s.searchState.offerResponse.Products[i].Interchangeable {
					offer.Interchangeable = append(
						offer.Interchangeable, fmt.Sprintf("%s:%s", alt.PartNumber, alt.CageCode),
					)
				}

				if len(resp.Entries[i].Plants) == 0 {
					s.searchState.offers = append(s.searchState.offers, offer)
				} else {
					for _, plant := range resp.Entries[i].Plants {
						newOffer := offer
						newOffer.QTY = plant.QTY
						newOffer.Warehouse = plant.Warehouse.Name

						s.searchState.offers = append(s.searchState.offers, newOffer)
					}
				}
			}
		},
	)
	s.plantsC.OnError(
		func(r *colly.Response, err error) {
			s.searchState.err = err
		},
	)
}

func (s SatAir) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer s.searchState.reset()

	u, _ := url.Parse(offerURL)
	q := u.Query()
	q.Set("pageSize", "20")
	q.Set("q", fmt.Sprintf("%s:relevance", partNumber))

	for page := 0; ; page++ {
		s.searchState.offerResponse.Products = nil
		s.searchState.addInfoResponse.ProductDetails = nil

		q.Set("currentPage", strconv.Itoa(page))
		u.RawQuery = q.Encode()

		if err := s.offerSearchC.Visit(u.String()); err != nil {
			return nil, err
		}

		type (
			productEntry struct {
				ID            string `json:"id"`
				QTY           int    `json:"quantity"`
				WarehouseCode string `json:"warehouseCode"`
			}
			params struct {
				ProductEntries []productEntry `json:"productEntries"`
			}
		)
		p := params{ProductEntries: make([]productEntry, len(s.searchState.offerResponse.Products))}
		for i := 0; i < len(s.searchState.offerResponse.Products); i++ {
			if strings.ToUpper(s.searchState.offerResponse.Products[i].PartNumber) != strings.ToUpper(partNumber) {
				break
			}
			p.ProductEntries[i] = productEntry{
				ID:            s.searchState.offerResponse.Products[i].ID,
				QTY:           1,
				WarehouseCode: "",
			}
		}

		if len(p.ProductEntries) == 0 {
			break
		}

		headers := http.Header{}
		headers.Set("Content-Type", "application/json")
		headers.Set(
			"User-Agent",
			"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
		)

		marshalledP, _ := json.Marshal(p)
		if err := s.addInfoC.Request(
			http.MethodPost, addInfoURL, bytes.NewReader(marshalledP), nil, headers,
		); err != nil {
			return nil, err
		}
		if err := s.plantsC.Request(
			http.MethodPost, plantsURL, bytes.NewReader(marshalledP), nil, headers,
		); err != nil {
			return nil, err
		}
	}

	return s.searchState.offers, s.searchState.err
}
