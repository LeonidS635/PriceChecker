package aerospareparts

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"regexp"
	"slices"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
)

const (
	titleInStock   = "In Stock"
	titleOnRequest = "On Request"
)

func (a AeroSpareParts) configureSearch() {
	a.searchC.AllowURLRevisit = true
	a.searchC.OnHTML(
		"body", func(body *colly.HTMLElement) {
			if partNumberEl := body.DOM.Find("span:contains(\"Part Number :\")"); partNumberEl.Length() > 0 {
				a.searchState.baseOffer.PartNumber = strings.TrimSpace(partNumberEl.Next().Text())
			}
			if descriptionEl := body.DOM.Find("span:contains(\"Description :\")"); descriptionEl.Length() > 0 {
				a.searchState.baseOffer.Description = descriptionEl.Next().Text()
			}
			if qtyEl := body.DOM.Find("span:contains(\"Stock available : \")"); qtyEl.Length() > 0 {
				if fields := strings.Fields(qtyEl.Next().Text()); len(fields) > 0 {
					a.searchState.baseOffer.QTY, _ = strconv.Atoi(fields[0])
				}
			}

			var titles []string
			body.DOM.Find("h4[class=\"Mine\"]").Each(
				func(_ int, title *goquery.Selection) {
					if strings.Contains(title.Text(), "in stock") {
						titles = append(titles, titleInStock)
					} else if strings.Contains(title.Text(), "on request") {
						titles = append(titles, titleOnRequest)
					} else {
						// Something wrong has happened
					}
				},
			)

			refsSet := make(map[string]struct{})
			body.DOM.Find("table[class=\"Grid\"]").Each(
				func(i int, table *goquery.Selection) {
					if i >= len(titles) {
						return
					}
					title := titles[i]

					if refs := table.Find("a[class=\"AutoquoteActionLink\"]"); refs.Length() == 0 {
						if title == titleOnRequest {
							var headers []string
							table.Find("th").Each(
								func(_ int, th *goquery.Selection) {
									headers = append(headers, strings.TrimSpace(th.Text()))
								},
							)

							table.Find("tbody > tr").Each(
								func(_ int, tr *goquery.Selection) {
									offer := a.searchState.baseOffer

									cols := table.Find("td")
									if idx := slices.Index(headers, "CD"); idx != -1 {
										offer.Condition = conditions.GetID(cols.Eq(idx).Text())
									}
									if idx := slices.Index(headers, "Incoterms"); idx != -1 {
										offer.Warehouse = cols.Eq(idx).Text()
									}
									if idx := slices.Index(headers, "Std Leadtime"); idx != -1 {
										offer.LeadTime = cols.Eq(idx).Text()
									}
									if idx := slices.Index(headers, "Stk qty"); idx != -1 {
										if parts := strings.Split(cols.Eq(idx).Text(), "*"); len(parts) > 0 {
											offer.QTY, _ = strconv.Atoi(parts[0])
										}
									}
									offer.OtherInformation = title

									a.searchState.offers = append(a.searchState.offers, offer)
								},
							)
						}
					} else {
						refs.Each(
							func(_ int, ref *goquery.Selection) {
								if href, ok := ref.Attr("href"); ok {
									href = baseURL + href

									parsedHRef, _ := url.Parse(href)
									q := parsedHRef.Query()
									q.Del("StockLocation")
									parsedHRef.RawQuery = q.Encode()

									if _, ok := refsSet[parsedHRef.String()]; !ok {
										quoteRef := a.searchState.quoteRequests[href]
										quoteRef.title = title
										a.searchState.quoteRequests[href] = quoteRef

										refsSet[parsedHRef.String()] = struct{}{}
									}
								}
							},
						)
					}
				},
			)
		},
	)
	a.searchC.OnError(
		func(r *colly.Response, err error) {
			a.searchState.err = err
		},
	)

	a.detailsC.AllowURLRevisit = true
	a.detailsC.OnHTML(
		"body", func(body *colly.HTMLElement) {
			payload := map[string]string{
				"PN":                      body.ChildAttr("input[name=\"PN\"]", "value"),
				"UOM":                     body.ChildAttr("input[name=\"UOM\"]", "value"),
				"COND":                    body.ChildAttr("input[name=\"COND\"]", "value"),
				"Country":                 body.ChildAttr("input[name=\"Country\"]", "value"),
				"StockAvailable":          body.ChildAttr("input[name=\"StockAvailable\"]", "value"),
				"StockAvailableToDisplay": body.ChildAttr("input[name=\"StockAvailableToDisplay\"]", "value"),
				"LT":                      body.ChildAttr("input[name=\"LT\"]", "value"),
				"RequestedQuantity":       "1",
				"submit":                  "Quote now",
			}
			ref := body.Request.URL.String()

			quoteRef := a.searchState.quoteRequests[ref]
			quoteRef.payload = payload
			a.searchState.quoteRequests[ref] = quoteRef
		},
	)
	a.detailsC.OnError(
		func(r *colly.Response, err error) {
			a.searchState.err = err
		},
	)

	a.quoteC.AllowURLRevisit = true
	a.quoteC.OnHTML(
		"body", func(body *colly.HTMLElement) {
			title := body.Request.Ctx.Get("title")

			newOffer := a.searchState.baseOffer
			if conditionEl := body.DOM.Find("label:contains(\"Condition :\") ~ span"); conditionEl.Length() > 0 {
				newOffer.Condition = conditions.GetID(conditionEl.Text())
			}
			if qtyEl := body.DOM.Find("label:contains(\"Stock available :\") ~ span"); qtyEl.Length() > 0 {
				newOffer.QTY, _ = strconv.Atoi(strings.TrimSpace(qtyEl.Text()))
			}
			newOffer.OtherInformation = title

			if table := body.DOM.Find("table[class=\"Grid\"]"); table.Length() > 0 {
				var headers []string
				table.Find("th").Each(
					func(_ int, th *goquery.Selection) {
						headers = append(headers, strings.TrimSpace(th.Text()))
					},
				)

				table.Find("tbody > tr").Each(
					func(_ int, tr *goquery.Selection) {
						offer := newOffer

						cols := tr.Find("td")
						if idx := slices.Index(headers, "QTY"); idx != -1 {
							if parts := strings.Fields(cols.Eq(idx).Text()); len(parts) > 0 {
								re := regexp.MustCompile("[^0-9]")
								offer.QTY, _ = strconv.Atoi(strings.TrimSpace(re.ReplaceAllString(parts[0], "")))
							}
						}
						if idx := slices.Index(headers, "Unit price"); idx != -1 {
							offer.Price, _ = utils.GetPriceFromString(cols.Eq(idx).Text())
						}
						if idx := slices.Index(headers, "Incoterms"); idx != -1 {
							offer.Warehouse = strings.TrimSpace(cols.Eq(idx).Text())
						}
						if idx := slices.Index(headers, "LT"); idx != -1 {
							lt := strings.TrimSpace(strings.Replace(cols.Eq(idx).Text(), "*", "", -1))
							if lt != "Rqst" && lt != "Stk" {
								offer.LeadTime = lt
							}
						}

						a.searchState.offers = append(a.searchState.offers, offer)
					},
				)
			} else {
				a.searchState.err = errors.New("session expired")
			}
		},
	)
	a.quoteC.OnError(
		func(r *colly.Response, err error) {
			a.searchState.err = err
		},
	)
}

func (a AeroSpareParts) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer a.searchState.reset()

	if err := a.searchC.Visit(fmt.Sprintf(searchURL, strings.ToUpper(partNumber))); err != nil {
		return nil, fmt.Errorf("failed to search: %w", err)
	}

	for ref := range a.searchState.quoteRequests {
		if err := a.detailsC.Visit(ref); err != nil {
			return nil, fmt.Errorf("failed to get deatils: %w", err)
		}
	}

	for _, quote := range a.searchState.quoteRequests {
		ctxWithTitle := colly.NewContext()
		ctxWithTitle.Put("title", quote.title)

		headers := http.Header{}
		headers.Set("Content-Type", "application/json; charset=utf-8")
		body, _ := json.Marshal(quote.payload)
		if err := a.quoteC.Request(
			http.MethodPost, quoteURL, bytes.NewReader(body), ctxWithTitle, headers,
		); err != nil {
			return nil, fmt.Errorf("failed to quote: %w", err)
		}
	}

	return a.searchState.offers, a.searchState.err
}
