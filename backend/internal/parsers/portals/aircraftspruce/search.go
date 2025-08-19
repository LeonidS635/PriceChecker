package aircraftspruce

import (
	"context"
	"fmt"
	"log"
	"net/url"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
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
					price, _ := strconv.ParseFloat(strings.Replace(strings.TrimSpace(parts[0]), "$", "", 1), 32)
					log.Println(priceText, price)
					offer.Price = float32(price)
				}
			}

			a.offers = append(a.offers, offer)
		},
	)

	a.searchC.OnError(
		func(r *colly.Response, err error) {
			a.err = err
		},
	)
}

func (a *AircraftSpruce) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer a.clearSearchResults()

	u := fmt.Sprintf(searchURL, url.PathEscape(partNumber))
	if err := a.searchC.Visit(u); err != nil {
		return nil, err
	}

	return a.offers, a.err
}

func (a *AircraftSpruce) clearSearchResults() {
	a.offers = []dto.Offer{}
	a.err = nil
}
