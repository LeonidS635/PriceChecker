package dasi

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net/http"
	"regexp"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/gocolly/colly/v2"
)

func (d Dasi) configureSearch() {
	d.searchC.SetClient(
		&http.Client{
			Transport: &http.Transport{
				TLSClientConfig: &tls.Config{
					RootCAs: rootCAs,
				},
			},
		},
	)
	d.searchC.AllowURLRevisit = true
	d.searchC.OnResponse(
		func(r *colly.Response) {
			type response struct {
				Products []struct {
					Name        string `json:"productName"`
					Description string `json:"productDescription"`
					Details     []struct {
						Price     float32 `json:"price"`
						Condition string  `json:"conditionCodeName"`
						QTY       int     `json:"quantityAv"`
						LeadTime  float32 `json:"leadTime"`
						Warehouse string  `json:"location"`
						TraceName string  `json:"traceName"`
						TraceTag  string  `json:"traceTag"`
					} `json:"productDetails"`
				} `json:"returnValue"`
			}
			resp := response{}

			if err := json.Unmarshal(r.Body, &resp); err != nil {
				d.searchState.err = err
				return
			}

			for _, product := range resp.Products {
				if strings.ToUpper(product.Name) == strings.ToUpper(d.searchState.requestedPN) {
					for _, details := range product.Details {
						var offer dto.Offer
						offer.PartNumber = product.Name
						offer.Description = product.Description
						offer.Condition = conditions.GetID(details.Condition)
						offer.Price = details.Price
						offer.QTY = details.QTY
						offer.LeadTime = fmt.Sprintf("%d days", int(details.LeadTime))
						offer.Warehouse = details.Warehouse
						offer.OtherInformation = fmt.Sprintf("Trace: %s | %s", details.TraceName, details.TraceTag)

						d.searchState.offers = append(d.searchState.offers, offer)
					}
				}
			}
		},
	)
	d.searchC.OnError(
		func(r *colly.Response, err error) {
			d.searchState.err = err
		},
	)
}

func (d Dasi) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer d.searchState.reset()

	d.searchState.requestedPN = partNumber

	type (
		params struct {
			Filters         []string `json:"filters"`
			PageSize        int      `json:"pageSize"`
			LastInvID       string   `json:"lastInvId"`
			LastSecInvID    string   `json:"lastSecInvId"`
			ConditionCodes  []string `json:"conditionCodes"`
			Locations       []string `json:"locations"`
			TraceTypes      []string `json:"traceTypes"`
			Tags            []string `json:"tags"`
			LeadTime        any      `json:"leadTime"`
			InventoryFilter string   `json:"inventoryFilter"`
			TypeOfSearch    string   `json:"typeOfSearch"`
			Exact           bool     `json:"exact"`
		}

		request struct {
			Namespace      string `json:"namespace"`
			Classname      string `json:"classname"`
			Method         string `json:"method"`
			IsContinuation bool   `json:"isContinuation"`
			Cacheable      bool   `json:"cacheable"`
			Params         params `json:"params"`
		}
	)
	req := request{
		Classname: "@udd/01pao00000Jqxvc",
		Method:    "searchParts",
		Params: params{
			Filters:         []string{regexp.MustCompile(`[^a-zA-Z0-9 ]+`).ReplaceAllString(partNumber, "")},
			PageSize:        500,
			ConditionCodes:  []string{},
			Locations:       []string{},
			TraceTypes:      []string{},
			Tags:            []string{},
			InventoryFilter: "all",
			TypeOfSearch:    "simple",
			Exact:           false,
		},
	}
	marshalledReq, _ := json.Marshal(&req)

	headers := http.Header{}
	headers.Set("Content-Type", "application/json")
	headers.Set(
		"User-Agent",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
	)
	if err := d.searchC.Request(http.MethodPost, searchURL, bytes.NewReader(marshalledReq), nil, headers); err != nil {
		d.searchState.err = err
	}
	return d.searchState.offers, d.searchState.err
}
