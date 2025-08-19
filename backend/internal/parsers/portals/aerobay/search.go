package aerobay

import (
	"context"
	"net/http"
	"net/url"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
)

const searchURL = "https://www.aero-bay.com/q"

func (a *Aerobay) configureSearch() {
	a.searchC.AllowURLRevisit = true

	a.searchC.OnHTML(
		"div[id=\"resultLists\"]", func(e *colly.HTMLElement) {
			e.ForEach(
				"div[class=\"parent_product_box_list\"]", func(_ int, partEl *colly.HTMLElement) {
					var offer dto.Offer

					offer.PartNumber = strings.TrimSpace(partEl.DOM.Find("h5").First().Text())
					partEl.DOM.Find("div[class*=\"product_infos_inside_product_box_list\"]").Each(
						func(i int, sel *goquery.Selection) {
							text := strings.TrimSpace(sel.Text())
							switch i {
							case 0:
								offer.Description = text
							case 1:
								offer.Condition = conditions.GetID(text)
							case 2:
								if text != "" {
									offer.QTY, _ = strconv.Atoi(text)
								}
							case 4:
								spans := sel.Find("span > span").Children()
								if spans.Length() >= 3 {
									major := strings.Replace(strings.TrimSpace(spans.Eq(1).Text()), " ", "", -1)
									minor := strings.Replace(strings.TrimSpace(spans.Eq(2).Text()), " ", "", -1)

									price, _ := strconv.ParseFloat(major+"."+minor, 32)
									offer.Price = float32(price)
								}
							case 6:
								offer.LeadTime = text
							}
						},
					)
					a.offers = append(a.offers, offer)
				},
			)
		},
	)
	a.searchC.OnError(
		func(r *colly.Response, err error) {
			if r.StatusCode != http.StatusNotFound {
				a.err = err
			}
		},
	)
}

func (a *Aerobay) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer a.clearSearchResults()

	u, err := url.Parse(searchURL)
	if err != nil {
		return nil, err
	}
	q := u.Query()
	q.Set("searchType", "PART_NUMBER")
	q.Set("item", partNumber)
	u.RawQuery = q.Encode()

	if err := a.searchC.Visit(u.String()); err != nil {
		return nil, err
	}
	return a.offers, a.err
}

func (a *Aerobay) clearSearchResults() {
	a.offers = []dto.Offer{}
	a.err = nil
}
