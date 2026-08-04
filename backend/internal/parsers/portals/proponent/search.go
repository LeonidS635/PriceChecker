package proponent

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
)

func (p Proponent) configureSearch() {
	p.partC.AllowURLRevisit = true
	p.partC.OnError(
		func(_ *colly.Response, err error) {
			p.searchState.err = err
		},
	)

	p.searchC.AllowURLRevisit = true
	p.searchC.OnResponse(
		func(r *colly.Response) {
			type response []struct {
				PartNumber  string `json:"Cust_part"`
				Description string `json:"Item_description1"`
				Price       string `json:"Price"`
				PriceBreaks string `json:"Price_breaks"`
				QTY         string `json:"QtyAvailable"`
				Warehouses  []struct {
					Name   string   `json:"DisplayName"`
					QTY    int      `json:"WhsQty"`
					Date   []string `json:"Due_date"`
					TotQTY []string `json:"TotQty"`
				} `json:"LstWarehouses"`
				LeadTime string `json:"leadtm"`
			}
			resp := response{}

			if err := json.Unmarshal(r.Body, &resp); err != nil {
				p.searchState.err = err
				return
			}
			if len(resp) == 0 {
				return
			}

			basePart := resp[0]

			var baseOffer dto.Offer
			baseOffer.PartNumber = basePart.PartNumber
			baseOffer.Description = basePart.Description
			if basePart.QTY == "Out of Stock" {
				baseOffer.OtherInformation = "Out of stock"
			} else {
				baseOffer.QTY, _ = strconv.Atoi(basePart.QTY)
			}
			baseOffer.Price, _ = utils.GetPriceFromString(basePart.Price)
			baseOffer.LeadTime = basePart.LeadTime
			if basePart.PriceBreaks != "No" {
				text := "Part has quantity sensitive pricing"
				if baseOffer.OtherInformation == "" {
					baseOffer.OtherInformation = text
				} else {
					baseOffer.OtherInformation = strings.Join([]string{baseOffer.OtherInformation, text}, "\n")
				}
			}
			for i := 1; i < len(resp); i++ {
				baseOffer.Interchangeable = append(baseOffer.Interchangeable, resp[i].PartNumber)
			}
			for _, w := range basePart.Warehouses {
				offer := baseOffer
				offer.Warehouse = strings.TrimPrefix(w.Name, "Warehouse: ")
				offer.QTY, _ = strconv.Atoi(basePart.QTY)
				if len(w.Date) > 0 && w.Date[0] != "" {
					text := fmt.Sprintf("Date Next In: %s", strings.Fields(w.Date[0])[0])
					if offer.OtherInformation == "" {
						offer.OtherInformation = text
					} else {
						offer.OtherInformation = strings.Join([]string{offer.OtherInformation, text}, "\n")
					}
				}
				if len(w.Date) > 0 && w.Date[0] != "" {
					text := fmt.Sprintf("QTY Due In: %s", w.TotQTY[0])
					if offer.OtherInformation == "" {
						offer.OtherInformation = text
					} else {
						offer.OtherInformation = strings.Join([]string{offer.OtherInformation, text}, "\n")
					}
				}

				p.searchState.offers = append(p.searchState.offers, offer)
			}
		},
	)
	p.searchC.OnError(
		func(_ *colly.Response, err error) {
			p.searchState.err = err
		},
	)

	p.detailsC.AllowURLRevisit = true
	p.detailsC.OnResponse(
		func(r *colly.Response) {
			type response struct {
				Details map[string]string `json:"d"`
			}
			resp := response{}

			if err := json.Unmarshal(r.Body, &resp); err != nil {
				p.searchState.err = err
				return
			}
			if len(resp.Details) != 1 {
				p.searchState.err = errors.New("unexpected format of part details response")
				return
			}

			if details, ok := resp.Details[p.searchState.requestedPN]; ok {
				div, err := goquery.NewDocumentFromReader(strings.NewReader(details))
				if err != nil {
					p.searchState.err = err
					return
				}

				if conditionEl := div.Find("strong:contains(\"Part Condition\")"); conditionEl.Length() > 0 {
					text := strings.TrimSpace(strings.ReplaceAll(conditionEl.Parent().Text(), conditionEl.Text(), ""))
					for i := 0; i < len(p.searchState.offers); i++ {
						p.searchState.offers[i].Condition = conditions.GetID(text)
					}
				}
			}
		},
	)
	p.detailsC.OnError(
		func(r *colly.Response, err error) {
			p.searchState.err = err
		},
	)
}

func (p Proponent) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer p.searchState.reset()

	headers := http.Header{}
	headers.Set("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
	headers.Set("Content-Type", "application/json")

	p.searchState.requestedPN = strings.ToUpper(partNumber)

	u, _ := url.Parse(partURL)
	q := u.Query()
	q.Set("id", strings.ToUpper(partNumber))
	u.RawQuery = q.Encode()
	if err := p.partC.Request(http.MethodGet, u.String(), nil, nil, headers); err != nil {
		log.Println("part err", err)
		return nil, err
	}

	marshalledSearchBody, _ := json.Marshal(struct {
		Nd     int64  `json:"nd"`
		Page   int    `json:"page"`
		Rows   int    `json:"rows"`
		Sidx   string `json:"sidx"`
		Sord   string `json:"sord"`
		Search bool   `json:"_search"`
	}{
		Nd:     time.Now().UnixMilli(),
		Page:   1,
		Rows:   20,
		Sidx:   "Item_site",
		Sord:   "asc",
		Search: false,
	})
	if err := p.searchC.Request(http.MethodPost, searchURL, bytes.NewReader(marshalledSearchBody), nil, headers); err != nil {
		log.Println("search err", err)
		return nil, err
	}
	if p.searchState.err != nil {
		log.Println("search err", p.searchState.err)
		return nil, p.searchState.err
	}

	marshalledDetailsBody, _ := json.Marshal(struct {
		PartIds []string `json:"partIds"`
	}{
		PartIds: []string{strings.ToUpper(partNumber)},
	})
	if err := p.detailsC.Request(http.MethodPost, detailsURL, bytes.NewReader(marshalledDetailsBody), nil, headers); err != nil {
		log.Println("details err", err)
		return nil, err
	}
	if p.searchState.err != nil {
		log.Println("details err", p.searchState.err)
		return nil, p.searchState.err
	}

	return p.searchState.offers, p.searchState.err
}
