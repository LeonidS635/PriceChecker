package scross

import (
	"context"
	"errors"
	"fmt"
	"strconv"
	"strings"

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
			details := e.DOM.Find("div[class=\"SearchedPNContainer Rounded T\"]")
			if len(details.Nodes) == 0 {
				s.searchState.err = errors.New("details not found")
				return
			}

			sections := details.Find("div[class=\"SearchedPNContent\"] > div")
			if sections.Length() != 3 {
				s.searchState.err = errors.New("sections not found")
				return
			}

			descriptionSection, priceSection := sections.Eq(1), sections.Eq(2)

			if descriptionSection.Find("span:contains(\"*PN not found*\")").Length() > 0 {
				return
			}

			var offer dto.Offer
			if pn, ok := descriptionSection.Find("meta[itemprop=\"sku\"]").Attr("content"); ok {
				offer.PartNumber = pn
			} else {
				s.searchState.err = errors.New("offer not found")
				return
			}
			if description, ok := descriptionSection.Find("meta[itemprop=\"description\"]").Attr("content"); ok {
				offer.Description = description
			} else {
				s.searchState.err = errors.New("offer not found")
			}
			if conditionEl := descriptionSection.Find("button[class=\"Circle Primary OptionSelected\"]"); conditionEl.Length() > 0 {
				offer.Condition = conditions.GetID(conditionEl.Text())
			}
			if price, ok := priceSection.Find("meta[itemprop=\"price\"]").Attr("content"); ok {
				offer.Price, _ = utils.GetPriceFromString(price)
			} else {
				s.searchState.err = errors.New("offer not found")
			}
			details.Find("h3:contains(\"Possible Alternate PNs\") ~ span a").Each(
				func(_ int, sel *goquery.Selection) {
					offer.Interchangeable = append(offer.Interchangeable, sel.Text())
				},
			)

			if table := priceSection.Find("table"); table.Length() > 0 {
				colsN := table.Find("tr:first-child td").Length()

				warehouses := make([]string, colsN)
				table.Find("th:contains(\"Warehouse\")").Each(
					func(_ int, th *goquery.Selection) {
						th.Parent().Find("td").Each(
							func(i int, td *goquery.Selection) {
								if i > colsN {
									s.searchState.err = errors.New("cols not found")
									return
								}
								warehouses[i] = td.Find("span[class=\"tooltiptext\"]").Text()
							},
						)
					},
				)

				availabilities := make([]string, colsN)
				table.Find("th:contains(\"Availability\")").Each(
					func(_ int, th *goquery.Selection) {
						th.Parent().Find("td").Each(
							func(i int, td *goquery.Selection) {
								if i > colsN {
									s.searchState.err = errors.New("cols not found")
									return
								}
								if parts := strings.Split(td.Text(), ": "); len(parts) > 0 {
									availabilities[i] = parts[len(parts)-1]
								}
							},
						)
					},
				)

				qtys := make([]string, colsN)
				table.Find("th:contains(\"Qty Available\")").Each(
					func(_ int, th *goquery.Selection) {
						th.Parent().Find("td").Each(
							func(i int, td *goquery.Selection) {
								if i > colsN {
									s.searchState.err = errors.New("cols not found")
									return
								}
								qtys[i] = td.Text()
							},
						)
					},
				)

				for i := 0; i < colsN; i++ {
					newOffer := offer
					newOffer.Warehouse = warehouses[i]
					newOffer.LeadTime = availabilities[i]
					if strings.Contains(strings.ToLower(qtys[i]), "out of stock") {
						newOffer.OtherInformation = "Out of stock"
					} else {
						newOffer.QTY, _ = strconv.Atoi(qtys[i])
					}
					s.searchState.offers = append(s.searchState.offers, newOffer)
				}
			} else {
				s.searchState.offers = append(s.searchState.offers, offer)
			}
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

	if err := s.searchC.Visit(fmt.Sprintf(searchURL, partNumber)); err != nil {
		return nil, err
	}
	return s.searchState.offers, s.searchState.err
}
