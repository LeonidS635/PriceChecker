package ajweventory

import (
	"context"
	"net/url"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
)

func (a AJWEventory) configureSearch() {
	a.searchC.AllowURLRevisit = true
	a.searchC.OnHTML(
		"div[class=\"grid-uniform\"] > div", func(e *colly.HTMLElement) {
			link := e.ChildAttr("a", "href")
			partNumber := strings.TrimSpace(e.DOM.Find("p").First().Text())
			if len(link) > 0 && strings.ToUpper(partNumber) == strings.ToUpper(a.searchState.requestedPN) {
				a.searchState.links = append(a.searchState.links, baseURL+link)
			}
		},
	)
	a.searchC.OnError(
		func(r *colly.Response, err error) {
			a.searchState.err = err
		},
	)

	a.partC.AllowURLRevisit = true
	a.partC.Async = true
	_ = a.partC.Limit(&colly.LimitRule{DomainGlob: baseURL, Parallelism: 10})
	a.partC.OnHTML(
		"body", func(e *colly.HTMLElement) {
			var offer dto.Offer

			offer.PartNumber = strings.TrimSpace(e.DOM.Find("h1[itemprop=\"name\"]").Text())
			offer.Description = strings.TrimSpace(e.DOM.Find("div[itemprop=\"description\"] > p > strong").Text())
			offer.Price, _ = utils.GetPriceFromString(e.ChildText("span[id=\"displayprice\"]"))
			if qtyEl := e.DOM.Find("div[id=\"variant-inventory\"]"); qtyEl.Length() > 0 {
				fields := strings.Fields(strings.TrimSpace(qtyEl.Text()))
				for i, word := range fields {
					if word == "have" && i+1 < len(fields) {
						offer.QTY, _ = strconv.Atoi(fields[i+1])
						break
					}
				}
			}
			if conditionEl := e.DOM.Find("p").FilterFunction(
				func(i int, s *goquery.Selection) bool {
					return strings.Contains(s.Text(), "Condition")
				},
			); conditionEl.Length() > 0 {
				text := strings.TrimSpace(conditionEl.Text())
				if parts := strings.SplitN(text, ": ", 2); len(parts) > 1 {
					offer.Condition = conditions.GetID(strings.TrimSpace(parts[1]))
				}
			}

			a.searchState.mu.Lock()
			a.searchState.offers = append(a.searchState.offers, offer)
			a.searchState.mu.Unlock()
		},
	)
	a.partC.OnError(
		func(r *colly.Response, err error) {
			a.searchState.mu.Lock()
			a.searchState.err = err
			a.searchState.mu.Unlock()
		},
	)
}

func (a AJWEventory) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer a.searchState.reset()

	a.searchState.requestedPN = partNumber

	for pageNumber := 1; ; pageNumber++ {
		u, _ := url.Parse(baseURL + "/a/search")
		q := u.Query()
		q.Set("q", partNumber)
		q.Set("page", strconv.Itoa(pageNumber))
		u.RawQuery = q.Encode()

		a.searchState.links = nil

		if err := a.searchC.Visit(u.String()); err != nil {
			return nil, err
		}

		if len(a.searchState.links) == 0 {
			break
		}

		for _, link := range a.searchState.links {
			if err := a.partC.Visit(link); err != nil {
				a.partC.Wait()
				return nil, err
			}
		}
		a.partC.Wait()

		if a.searchState.err != nil {
			return nil, a.searchState.err
		}
	}

	return a.searchState.offers, a.searchState.err
}
