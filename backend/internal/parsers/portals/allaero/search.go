package allaero

import (
	"context"
	"fmt"
	"net/http"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/gocolly/colly/v2"
)

func (a AllAero) configureSearch() {
	a.searchC.AllowURLRevisit = true

	a.searchC.OnHTML(
		"body", func(e *colly.HTMLElement) {
			var offer dto.Offer

			offer.PartNumber = strings.TrimSpace(e.ChildText("span[itemprop=\"identifier\"]"))
			offer.Description = strings.TrimSpace(e.ChildText("span[itemprop=\"name\"]"))
			if condition := strings.TrimSpace(e.ChildText("td[data-title=\"Condition / Certification\"]")); condition != "" && condition != "Any" {
				offer.Condition = conditions.GetID(condition)
			}
			if leadTime := strings.TrimSpace(e.ChildText("td[data-title=\"Release:\"]")); leadTime != "" && leadTime != "Any" {
				offer.LeadTime = leadTime
			}
			if qtyText := strings.TrimSpace(e.ChildText("td[data-title=\"Stock:\"]")); qtyText != "" {
				if fields := strings.Fields(qtyText); len(fields) > 0 {
					offer.QTY, _ = strconv.Atoi(fields[0])
				}
			}
			offer.Price, _ = utils.GetPriceFromString(e.ChildText("td[data-title=\"Price\"] > div[id=\"Price_0\"] > span[class=\"value\"]"))

			e.ForEach(
				"div[class$=\"alternate-part\"]", func(_ int, alt *colly.HTMLElement) {
					if links := alt.ChildAttrs("a", "href"); len(links) >= 2 {
						altText := alt.ChildText("a:nth-of-type(2) span")
						if altText != "" {
							offer.Interchangeable = append(offer.Interchangeable, strings.TrimSpace(altText))
						}
					}
				},
			)

			a.searchState.offers = append(a.searchState.offers, offer)
		},
	)
	a.searchC.OnError(
		func(r *colly.Response, err error) {
			if r.StatusCode != http.StatusNotFound {
				a.searchState.err = err
			}
		},
	)
}

func (a AllAero) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer a.searchState.reset()

	if err := a.searchC.Visit(fmt.Sprintf(searchURL, partNumber)); err != nil {
		return nil, err
	}
	return a.searchState.offers, a.searchState.err
}
