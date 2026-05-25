package satair

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/gocolly/colly/v2"
)

const batchSize = 5

func (s SatAir) configureSearch() {
	s.offerSearchC.AllowURLRevisit = true
	s.offerSearchC.OnResponse(
		func(r *colly.Response) {
			if err := json.Unmarshal(r.Body, &s.searchState); err != nil {
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
			if err := json.Unmarshal(r.Body, &s.searchState); err != nil {
				s.searchState.err = err
				return
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
			if err := json.Unmarshal(r.Body, &s.searchState); err != nil {
				s.searchState.err = err
				return
			}
		},
	)
	s.plantsC.OnError(
		func(r *colly.Response, err error) {
			s.searchState.err = err
		},
	)
}

func (s SatAir) formOffers(batch int) {
	productsMap := make(map[string]mainProductInfo)
	productsDetailsMap := make(map[string]additionalProductInfo)
	productsPlantsMap := make(map[string]plantsInfo)
	for _, product := range s.searchState.OfferResponse {
		productsMap[product.ProductID] = product
	}
	for _, product := range s.searchState.AddInfoResponse {
		productsDetailsMap[product.ProductID] = product
	}
	for _, product := range s.searchState.PlantsResponse {
		productsPlantsMap[product.ProductID] = product
	}

	for i, j := 0, batch*batchSize; i < len(s.searchState.AddInfoResponse) && j < len(s.searchState.OfferResponse); i, j = i+1, j+1 {
		productID := s.searchState.OfferResponse[j].ProductID

		var offer dto.Offer
		offer.PartNumber = productsMap[productID].PartNumber
		offer.Description = productsMap[productID].Description
		offer.Condition = conditions.GetID(productsMap[productID].Condition)
		offer.QTY = productsDetailsMap[productID].Details.QTY
		offer.Price = productsDetailsMap[productID].Details.Price.Value
		offer.Warehouse = productsDetailsMap[productID].Details.Warehouse.Name
		if offer.Warehouse == "" {
			offer.Warehouse = productsDetailsMap[productID].Details.Shop.Location
		}
		if !productsDetailsMap[productID].Details.InStock {
			if len(productsDetailsMap[productID].Details.Availabilities) > 0 {
				offer.LeadTime = productsDetailsMap[productID].Details.Availabilities[0].Date
			}
		}
		for _, alt := range productsMap[productID].Interchangeable {
			offer.Interchangeable = append(
				offer.Interchangeable, fmt.Sprintf("%s:%s", alt.PartNumber, alt.CageCode),
			)
		}

		log.Println("PLANTS FOR OFFER", offer, ":", productsPlantsMap[productID].Plants)
		if len(productsPlantsMap[productID].Plants) == 0 {
			s.searchState.offers = append(s.searchState.offers, offer)
		} else {
			for _, plant := range productsPlantsMap[productID].Plants {
				newOffer := offer
				newOffer.QTY = plant.QTY
				newOffer.Warehouse = plant.Warehouse.Name

				s.searchState.offers = append(s.searchState.offers, newOffer)
			}
		}
	}
}

func (s SatAir) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer s.searchState.reset()

	u, _ := url.Parse(offerURL)
	q := u.Query()
	q.Set("pageSize", "20")
	q.Set("q", fmt.Sprintf("%s:relevance", partNumber))

	for page := 0; ; page++ {
		s.searchState.OfferResponse = nil
		s.searchState.AddInfoResponse = nil
		s.searchState.PlantsResponse = nil

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
		p := params{ProductEntries: make([]productEntry, 0, len(s.searchState.OfferResponse))}
		for i := 0; i < len(s.searchState.OfferResponse); i++ {
			if !strings.EqualFold(s.searchState.OfferResponse[i].PartNumber, partNumber) {
				break
			}
			p.ProductEntries = append(
				p.ProductEntries, productEntry{
					ID:            s.searchState.OfferResponse[i].ProductID,
					QTY:           1,
					WarehouseCode: "",
				},
			)
		}

		if len(p.ProductEntries) == 0 {
			break
		}

		batchCtx := colly.NewContext()
		for batch := 0; batch < (len(p.ProductEntries)+batchSize-1)/batchSize; batch++ {
			paramsToMarshall := params{
				ProductEntries: p.ProductEntries[batch*batchSize : min((batch+1)*batchSize, len(p.ProductEntries))],
			}
			marshalledP, _ := json.Marshal(paramsToMarshall)

			newHeaders := func() http.Header {
				h := http.Header{}
				h.Set("Content-Type", "application/json")
				h.Set(
					"User-Agent",
					"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
				)
				return h
			}

			if err := s.addInfoC.Request(
				http.MethodPost, addInfoURL, bytes.NewReader(marshalledP), batchCtx, newHeaders(),
			); err != nil {
				return nil, err
			}
			if err := s.plantsC.Request(
				http.MethodPost, plantsURL, bytes.NewReader(marshalledP), batchCtx, newHeaders(),
			); err != nil {
				return nil, err
			}

			s.formOffers(batch)
		}
	}

	return s.searchState.offers, s.searchState.err
}
