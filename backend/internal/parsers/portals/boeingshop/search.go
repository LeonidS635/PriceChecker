package boeingshop

import (
	"context"
	"encoding/json"
	"log"
	"net/url"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/gocolly/colly/v2"
)

func (b BoeingShop) configureSearch() {
	b.searchC.AllowURLRevisit = true
	b.searchC.OnRequest(
		func(r *colly.Request) {
			r.Headers.Set(
				"User-Agent",
				"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
			)
		},
	)
	b.searchC.OnResponse(
		func(r *colly.Response) {
			type response struct {
				Products []struct {
					OemPartNumber string `json:"oemPartNumber"`
					Name          string `json:"name"`
					InStock       bool   `json:"inStock"`
				} `json:"products"`
			}
			resp := response{}

			if err := json.Unmarshal(r.Body, &resp); err != nil {
				b.searchState.err = err
				return
			}

			if len(resp.Products) == 0 {
				b.searchState.exactMatch = false
				return
			}

			for _, product := range resp.Products {
				if strings.ToUpper(product.OemPartNumber) != strings.ToUpper(b.searchState.requestedPN) {
					b.searchState.exactMatch = false
					return
				}

				var offer dto.Offer

				offer.PartNumber = product.OemPartNumber
				offer.Description = product.Name
				if product.InStock {
					offer.OtherInformation = "In stock"
				} else {
					offer.OtherInformation = "Out of stock"
				}

				b.searchState.offers = append(b.searchState.offers, offer)
			}
		},
	)
	b.searchC.OnError(
		func(r *colly.Response, err error) {
			log.Println(r.StatusCode, err)
			b.searchState.err = err
		},
	)
}

func (b BoeingShop) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer b.searchState.reset()

	b.searchState.requestedPN = partNumber

	u, _ := url.Parse(searchURL)
	q := u.Query()
	q.Set("query", strings.ToLower(partNumber))
	q.Set("fields", "DEFAULT")
	q.Set("pageSize", "20")
	q.Set("lang", "en_US")
	q.Set("curr", "USD")

	for page := 0; b.searchState.exactMatch; page++ {
		q.Set("currentPage", strconv.Itoa(page))
		u.RawQuery = q.Encode()

		if err := b.searchC.Visit(u.String()); err != nil {
			return nil, err
		}
	}
	return b.searchState.offers, b.searchState.err
}
