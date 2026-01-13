package wencor

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/gocolly/colly/v2"
)

func (w Wencor) configureSearch() {
	w.searchC.AllowURLRevisit = true
	w.searchC.OnResponse(
		func(r *colly.Response) {
			type response struct {
				Items []struct {
					PartNumber string `json:"name"`
					ID         string `json:"itemNumber"`
				} `json:"itemResponseList"`
			}
			resp := response{}

			if err := json.Unmarshal(r.Body, &resp); err != nil {
				w.searchState.err = err
				return
			}

			for _, item := range resp.Items {
				if strings.EqualFold(item.PartNumber, w.searchState.requestedPN) {
					w.searchState.partID = item.ID
					return
				}
			}
		},
	)
	w.searchC.OnError(
		func(_ *colly.Response, err error) {
			w.searchState.err = err
		},
	)

	w.detailsC.AllowURLRevisit = true
	w.detailsC.OnResponse(
		func(r *colly.Response) {
			type response struct {
				PartNumber  string `json:"name"`
				Description string `json:"description"`
				Price       struct {
					Gross float32 `json:"gross"`
				} `json:"price"`
				StockLevel []struct {
					QTY       float32 `json:"quantity"`
					Warehouse string  `json:"warehouse"`
				} `json:"stockLevel"`
			}
			resp := response{}

			if err := json.Unmarshal(r.Body, &resp); err != nil {
				w.searchState.err = err
				return
			}

			w.searchState.baseOffer.PartNumber = resp.PartNumber
			w.searchState.baseOffer.Description = resp.Description
			w.searchState.baseOffer.Condition = conditions.NE
			w.searchState.baseOffer.Price = resp.Price.Gross
			if len(resp.StockLevel) > 0 {
				for _, stockLevel := range resp.StockLevel {
					offer := w.searchState.baseOffer
					offer.QTY = int(stockLevel.QTY)
					offer.Warehouse = stockLevel.Warehouse
					w.searchState.offers = append(w.searchState.offers, offer)
				}
			} else {
				w.searchState.offers = append(w.searchState.offers, w.searchState.baseOffer)
			}
		},
	)
	w.detailsC.OnError(
		func(_ *colly.Response, err error) {
			w.searchState.err = err
		},
	)

	w.attributesC.AllowURLRevisit = true
	w.attributesC.OnResponse(
		func(r *colly.Response) {
			type response []struct {
				Key    string   `json:"key"`
				Values []string `json:"values"`
			}
			resp := response{}

			if err := json.Unmarshal(r.Body, &resp); err != nil {
				w.searchState.err = err
				return
			}

			for _, v := range resp {
				switch v.Key {
				case "ItemLeadTime":
					if len(v.Values) != 1 {
						w.searchState.err = errors.New("unexpected length of values (lead time)")
						return
					}
					for i := 0; i < len(w.searchState.offers); i++ {
						w.searchState.offers[i].LeadTime = v.Values[0]
					}
				case "RelatedItems":
					if len(v.Values) != 1 {
						w.searchState.err = errors.New("unexpected length of values (interchangeable)")
						return
					}
					for _, part := range strings.Split(v.Values[0], ";") {
						part = strings.TrimSpace(part)
						for i := 0; i < len(w.searchState.offers); i++ {
							w.searchState.offers[i].Interchangeable = append(
								w.searchState.offers[i].Interchangeable, part,
							)
						}
					}
				}
			}
		},
	)
	w.attributesC.OnError(
		func(_ *colly.Response, err error) {
			w.searchState.err = err
		},
	)
}

func (w Wencor) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer w.searchState.reset()

	w.searchState.requestedPN = partNumber

	u, _ := url.Parse(searchURL)
	q := u.Query()
	q.Set("start", "1")
	q.Set("size", "24")
	q.Set("search", strings.ToUpper(partNumber))
	q.Set("includePrices", "false")
	q.Set("includeStockLevel", "false")
	q.Set("hasChanges", "true")
	u.RawQuery = q.Encode()
	if err := w.searchC.Visit(u.String()); err != nil {
		return nil, err
	}
	if w.searchState.err != nil {
		return nil, w.searchState.err
	}
	if w.searchState.partID == "" {
		return nil, nil
	}

	u, _ = url.Parse(fmt.Sprintf(detailsURL, w.searchState.partID))
	q = u.Query()
	q.Set("includeStockLevel", "true")
	q.Set("includePriceBreaks", "true")
	u.RawQuery = q.Encode()
	if err := w.detailsC.Visit(u.String()); err != nil {
		return nil, err
	}
	if w.searchState.err != nil {
		return nil, w.searchState.err
	}

	u, _ = url.Parse(fmt.Sprintf(attributesURL, w.searchState.partID))
	q = u.Query()
	q.Set("size", "-1")
	u.RawQuery = q.Encode()
	if err := w.attributesC.Visit(u.String()); err != nil {
		return nil, err
	}

	return w.searchState.offers, w.searchState.err
}
