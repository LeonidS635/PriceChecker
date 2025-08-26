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

func (a *AeroBay) configureSearch() {
	a.searchC.AllowURLRevisit = true

	a.searchC.OnHTML(
		"body", func(body *colly.HTMLElement) {
			parts := body.DOM.Find("div[class=\"parent_product_box_list\"]").EachIter()
			for _, p := range parts {
				var offer dto.Offer

				offer.PartNumber = strings.TrimSpace(p.Find("h5").First().Text())
				if strings.ToUpper(offer.PartNumber) != strings.ToUpper(a.searchState.requestedPN) {
					a.searchState.exactMatch = false
					return
				}

				p.Find("div[class*=\"product_infos_inside_product_box_list\"]").Each(
					func(i int, sel *goquery.Selection) {
						text := strings.TrimSpace(sel.Text())
						switch i {
						case 0:
							offer.Description, _ = sel.Find("p").Attr("title")
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
							if text != "N/A" {
								offer.LeadTime = text
							}
						}
					},
				)
				a.searchState.offers = append(a.searchState.offers, offer)
			}
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

func (a *AeroBay) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer a.searchState.reset()

	a.searchState.requestedPN = partNumber

	u, _ := url.Parse(searchURL)
	q := u.Query()
	q.Set("searchType", "PART_NUMBER")
	q.Set("item", strings.ToUpper(partNumber))
	u.RawQuery = q.Encode()

	if err := a.searchC.Visit(u.String()); err != nil {
		return nil, err
	}
	return a.searchState.offers, a.searchState.err
}
