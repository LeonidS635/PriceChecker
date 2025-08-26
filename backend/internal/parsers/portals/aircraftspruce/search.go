package aircraftspruce

import (
	"context"
	"fmt"
	"net/url"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/gocolly/colly/v2"
)

func (a *AircraftSpruce) configureSearch() {
	a.searchC.AllowURLRevisit = true

	a.searchC.OnHTML(
		"div[class=\"prDetailRight\"]", func(e *colly.HTMLElement) {
			var offer dto.Offer

			if partNumEl := e.DOM.Find("div[class=\"prModel\""); partNumEl.Length() > 0 {
				text := strings.TrimSpace(partNumEl.Text())
				if lines := strings.Split(text, "\n"); len(lines) >= 2 {
					fields := strings.Fields(lines[1])
					if len(fields) > 0 {
						offer.PartNumber = fields[len(fields)-1]
					}
				}
			}
			if descEl := e.DOM.Find("h2").First(); descEl.Length() > 0 {
				offer.Description = strings.TrimSpace(descEl.Text())
			}
			if priceEl := e.DOM.Find("div[class=\"prPrice\"] div[id=\"np\"]"); priceEl.Length() > 0 {
				priceText := strings.TrimSpace(priceEl.Text())
				if parts := strings.Split(priceText, "/"); len(parts) > 0 {
					offer.Price, _ = utils.GetPriceFromString(parts[0])
				}
			}

			a.searchState.offers = append(a.searchState.offers, offer)
		},
	)
	a.searchC.OnError(
		func(r *colly.Response, err error) {
			a.searchState.err = err
		},
	)
}

func (a *AircraftSpruce) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer a.searchState.reset()

	u := fmt.Sprintf(searchURL, url.PathEscape(partNumber))
	if err := a.searchC.Visit(u); err != nil {
		return nil, err
	}
	return a.searchState.offers, a.searchState.err
}
