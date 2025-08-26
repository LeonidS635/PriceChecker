package lasaero

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
)

func (l LASAero) configureSearch() {
	l.searchC.AllowURLRevisit = true
	l.searchC.OnHTML(
		"body", func(e *colly.HTMLElement) {
			partNumber := e.ChildText("h1")
			if partNumber == "" {
				l.searchState.err = errors.New("no part number found")
				return
			}

			table := e.DOM.Find("table").First()
			if table.Length() == 0 {
				l.searchState.err = errors.New("table with part details not found (perhaps site layout was changed)")
				return
			}

			var offer dto.Offer
			offer.PartNumber = partNumber
			table.Find("td").Each(
				func(i int, td *goquery.Selection) {
					text := strings.TrimSpace(td.Text())
					switch i {
					case 1:
						offer.Description = text
					case 3:
						offer.QTY, _ = strconv.Atoi(text)
					case 5:
						qtyInOrder, _ := strconv.Atoi(text)
						if qtyInOrder != 0 {
							offer.OtherInformation = fmt.Sprintf("QTY in order: %d", qtyInOrder)
						}
					case 7:
						splittedPrice := strings.Fields(text)
						if len(splittedPrice) != 4 {
							l.searchState.err = errors.New("splitted price not found (perhaps site layout was changed)")
							return
						}
						offer.Price, _ = utils.GetPriceFromString(splittedPrice[1])
					case 9:
						offer.LeadTime = text
					}
				},
			)
			l.searchState.offers = append(l.searchState.offers, offer)
		},
	)
	l.searchC.OnError(
		func(r *colly.Response, err error) {
			if r.StatusCode != http.StatusNotFound {
				l.searchState.err = err
			}
		},
	)
}

func (l LASAero) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer l.searchState.reset()

	if err := l.searchC.Visit(fmt.Sprintf(searchURL, partNumber)); err != nil {
		return nil, err
	}
	return l.searchState.offers, l.searchState.err
}
