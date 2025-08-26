package airpowerinc

import (
	"context"
	"encoding/json"
	"math/rand"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
)

func (a AirPowerInc) configureSearch() {
	a.searchC.AllowURLRevisit = true
	a.searchC.OnResponse(
		func(r *colly.Response) {
			type responseData struct {
				Data []struct {
					Sku               string `json:"Sku"`
					Name              string `json:"Name"`
					Price             string `json:"Price"`
					StockMessage      string `json:"StockMessage"`
					AlternateProducts string `json:"AlternateProducts"`
				} `json:"data"`
			}

			resp := responseData{}
			if err := json.Unmarshal(r.Body, &resp); err != nil {
				a.searchState.err = err
				return
			}

			if len(resp.Data) == 0 {
				a.searchState.exactMatch = false
				return
			}

			for _, part := range resp.Data {
				if strings.ToUpper(part.Sku) != strings.ToUpper(a.searchState.requestedPN) {
					a.searchState.exactMatch = false
					return
				}

				var offer dto.Offer

				offer.PartNumber = part.Sku
				if skuAndDescription := strings.SplitN(part.Name, " ", 2); len(skuAndDescription) == 2 {
					offer.Description = strings.TrimSpace(skuAndDescription[1])
				} else {
					offer.Description = part.Name
				}
				if priceReader, err := goquery.NewDocumentFromReader(strings.NewReader(part.Price)); err == nil {
					offer.Price, _ = utils.GetPriceFromString(priceReader.Text())
				}
				if availability := strings.SplitN(part.StockMessage, "\n", 2); len(availability) > 0 {
					qtyAndCondition := strings.Split(availability[0], "-")
					if len(qtyAndCondition) == 2 {
						qty := strings.TrimSpace(strings.Replace(qtyAndCondition[0], "in stock", "", -1))
						offer.QTY, _ = strconv.Atoi(qty)

						offer.Condition = conditions.GetID(qtyAndCondition[1])
					}

					if len(availability) == 2 {
						offer.OtherInformation = availability[1]
					}
				}
				if alternatesReader, err := goquery.NewDocumentFromReader(strings.NewReader(part.AlternateProducts)); err == nil {
					alternatesReader.Find("a[class=\"ap-link\"]").Each(
						func(_ int, sel *goquery.Selection) {
							ref, _ := sel.Attr("href")
							offer.Interchangeable = append(
								offer.Interchangeable, strings.ToUpper(strings.TrimPrefix(ref, "/")),
							)
						},
					)
				}

				a.searchState.offers = append(a.searchState.offers, offer)
			}
		},
	)

	a.searchC.OnError(
		func(r *colly.Response, err error) {
			if r.StatusCode == http.StatusTooManyRequests {
				retriesN := 0
				if retries, exists := r.Request.Ctx.GetAny("retries").(int); exists {
					retriesN = retries
				}
				retriesN++

				if retriesN < 5 {
					time.Sleep((1<<retriesN)*time.Second + time.Duration(rand.Intn(10)*100)*time.Millisecond)

					r.Request.Ctx.Put("retries", retriesN)
					_ = a.searchC.Request(
						http.MethodPost, r.Request.URL.String(), r.Request.Body, r.Request.Ctx, nil,
					)
					return
				}
			}

			a.searchState.err = err
		},
	)
}

func (a AirPowerInc) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer a.searchState.reset()

	a.searchState.requestedPN = partNumber

	type (
		search struct {
			Value string `json:"value"`
			Regex bool   `json:"regex"`
		}
		columnSettings struct {
			Data       string `json:"data"`
			Name       string `json:"name"`
			Searchable bool   `json:"searchable"`
			Orderable  bool   `json:"orderable"`
			Search     search `json:"search"`
		}
		tableSettings struct {
			Draw    int              `json:"draw"`
			Columns []columnSettings `json:"columns"`
			Order   []string         `json:"order"`
			Start   int              `json:"start"`
			Length  int              `json:"length"`
			Search  search           `json:"search"`
		}
	)
	table := tableSettings{
		Draw: 1,
		Columns: []columnSettings{
			{
				Data: "ImageElement", Name: "", Searchable: true, Orderable: false, Search: search{
					Value: "", Regex: false,
				},
			},
			{
				Data: "Sku", Name: "", Searchable: true, Orderable: false, Search: search{
					Value: "", Regex: false,
				},
			},
			{
				Data: "Name", Name: "", Searchable: true, Orderable: false, Search: search{
					Value: "", Regex: false,
				},
			},
			{
				Data: "Description", Name: "", Searchable: true, Orderable: false, Search: search{
					Value: "", Regex: false,
				},
			},
			{
				Data: "StockMessage", Name: "", Searchable: true, Orderable: false, Search: search{
					Value: "", Regex: false,
				},
			},
			{
				Data: "Price", Name: "", Searchable: true, Orderable: false, Search: search{
					Value: "", Regex: false,
				},
			},
			{
				Data: "Buttons", Name: "", Searchable: true, Orderable: false, Search: search{
					Value: "", Regex: false,
				},
			},
		},
		Order:  []string{},
		Start:  0,
		Length: 10,
		Search: search{
			Value: "", Regex: false,
		},
	}

	for ; a.searchState.exactMatch; table.Start += table.Length {
		tableStr, _ := json.Marshal(table)
		_ = tableStr

		if err := a.searchC.Post(
			tableURL, map[string]string{
				"myDataTableParameter": string(tableStr),
				"searchValue":          strings.ToUpper(partNumber),
			},
		); err != nil {
			return nil, err
		}
	}
	return a.searchState.offers, a.searchState.err
}
