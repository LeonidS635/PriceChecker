package skyspares

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
)

func (s SkySpares) configureSearch() {
	s.searchC.AllowURLRevisit = true
	s.searchC.OnHTML(
		"body", func(body *colly.HTMLElement) {
			if partNumberEl := body.DOM.Find("h1"); partNumberEl.Length() > 0 {
				s.searchState.baseOffer.PartNumber = partNumberEl.Text()
			} else {
				s.searchState.err = errors.New("no part number found")
				return
			}
			if descAndQTY := body.DOM.Find("table > tbody > tr"); descAndQTY.Length() == 2 {
				s.searchState.baseOffer.Description = descAndQTY.Eq(0).Find("td").Eq(1).Text()
				s.searchState.baseOffer.QTY, _ = strconv.Atoi(descAndQTY.Eq(1).Find("td").Eq(1).Text())
			} else {
				s.searchState.err = errors.New("no table found")
				return
			}
		},
	)
	s.searchC.OnError(
		func(r *colly.Response, err error) {
			if r.StatusCode != http.StatusNotFound {
				s.searchState.err = err
			}
		},
	)

	s.detailsC.AllowURLRevisit = true
	s.detailsC.OnHTML(
		"body", func(body *colly.HTMLElement) {
			batches := body.DOM.Find("div[class=\"batch-list-for-condition\"] > div")
			if batches.Length() == 0 {
				s.searchState.offers = append(s.searchState.offers, s.searchState.baseOffer)
				return
			}

			batches.Each(
				func(_ int, sel *goquery.Selection) {
					offer := s.searchState.baseOffer
					if conditionEl := sel.Find("div[class=\"col-2\"] > span[class=\"hidden-xs\"]"); conditionEl.Length() > 0 {
						offer.Condition = conditions.GetID(conditionEl.Text())
					} else {
						s.searchState.err = errors.New("no condition found")
						return
					}
					if qtyEl := sel.Find("div[class=\"col-4 text-right\"]"); qtyEl.Length() > 0 {
						offer.QTY, _ = strconv.Atoi(qtyEl.Text())
					} else {
						s.searchState.err = errors.New("no QTY found")
						return
					}
					if priceEl := sel.Find("div[class=\"col-5 text-right\"]"); priceEl.Length() > 0 {
						if priceFields := strings.Fields(priceEl.Text()); len(priceFields) >= 2 {
							offer.Price, _ = utils.GetPriceFromString(priceFields[1])
						} else {
							s.searchState.err = errors.New("no price found")
							return
						}
					} else {
						s.searchState.err = errors.New("no price found")
						return
					}
					s.searchState.offers = append(s.searchState.offers, offer)
				},
			)
		},
	)
	s.detailsC.OnError(
		func(r *colly.Response, err error) {
			s.searchState.err = err
		},
	)
}

func (s SkySpares) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer s.searchState.reset()

	if err := s.searchC.Visit(fmt.Sprintf(searchURL, partNumber)); err != nil {
		return nil, err
	}

	u, _ := url.Parse(fmt.Sprintf(searchURL, partNumber))
	q := u.Query()
	q.Set("inline", "true")
	u.RawQuery = q.Encode()

	_ = s.detailsC.SetCookies(
		fmt.Sprintf(searchURL, partNumber), []*http.Cookie{
			{
				Name:  "currency",
				Value: "USD",
			},
		},
	)
	if err := s.detailsC.Visit(u.String()); err != nil {
		return nil, err
	}
	return s.searchState.offers, s.searchState.err
}
