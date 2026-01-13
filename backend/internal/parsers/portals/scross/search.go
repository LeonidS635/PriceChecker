package scross

import (
	"context"
	"net/url"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
)

func (s SCross) configureSearch() {
	s.searchC.AllowURLRevisit = true
	s.searchC.OnHTML(
		"body", func(e *colly.HTMLElement) {
			partPage := e.DOM.Find("div[itemtype=\"https://schema.org/Product\"]")
			if partPage.Length() == 0 {
				return
			}

			var offer dto.Offer
			offer.PartNumber = partPage.Find("meta[itemprop=\"mpn\"]").AttrOr("content", "")
			offer.Description = partPage.Find("meta[itemprop=\"description\"]").AttrOr("content", "")
			offer.Price, _ = utils.GetPriceFromString(partPage.Find("meta[itemprop=\"price\"]").AttrOr("content", ""))
			offer.Condition = conditions.GetID(partPage.Find("td[id=\"PNConditionID\"]").Text())
			offer.OtherInformation = partPage.Find("span[class*=\"status-positive\"], span[class*=\"status-negative\"]").First().Text()

			partPage.Find("article").Find("div[class*=\"card-info\"]").Each(
				func(_ int, card *goquery.Selection) {
					offer.Interchangeable = append(offer.Interchangeable, card.Find("h3").First().Text())
				},
			)

			s.searchState.offers = append(s.searchState.offers, offer)
		},
	)
	s.searchC.OnError(
		func(r *colly.Response, err error) {
			s.searchState.err = err
		},
	)
}

func (s SCross) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer s.searchState.reset()

	u, _ := url.Parse(searchURL)
	q := u.Query()
	q.Set("pn", partNumber)
	u.RawQuery = q.Encode()

	if err := s.searchC.Visit(u.String()); err != nil {
		return nil, err
	}
	return s.searchState.offers, s.searchState.err
}
