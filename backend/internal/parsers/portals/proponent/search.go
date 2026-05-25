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

			log.Println("BODYx", r.Body)

			if err := json.Unmarshal(r.Body, &resp); err != nil {
				p.searchState.err = err
				return
			}
			if len(resp) > 1 {
				p.searchState.err = errors.New("unexpected format of part response")
				return
			}
			if len(resp) == 0 {
				return
			}

			log.Println("SEARCH RESULT", resp)

			var baseOffer dto.Offer
			baseOffer.PartNumber = resp[0].PartNumber
			baseOffer.Description = resp[0].Description
			if resp[0].QTY == "Out of Stock" {
				baseOffer.OtherInformation = "Out of stock"
			} else {
				baseOffer.QTY, _ = strconv.Atoi(resp[0].QTY)
			}
			baseOffer.Price, _ = utils.GetPriceFromString(resp[0].Price)
			baseOffer.LeadTime = resp[0].LeadTime
			if resp[0].PriceBreaks != "No" {
				text := "Part has quantity sensitive pricing"
				if baseOffer.OtherInformation == "" {
					baseOffer.OtherInformation = text
				} else {
					baseOffer.OtherInformation = strings.Join([]string{baseOffer.OtherInformation, text}, "\n")
				}
			}
			for _, w := range resp[0].Warehouses {
				offer := baseOffer
				offer.Warehouse = strings.TrimPrefix(w.Name, "Warehouse: ")
				offer.QTY, _ = strconv.Atoi(resp[0].QTY)
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

			log.Println("DETAILS", resp)

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

	p.searchState.requestedPN = strings.ToUpper(partNumber)

	u, _ := url.Parse(partURL)
	q := u.Query()
	q.Set("id", strings.ToUpper(partNumber))
	u.RawQuery = q.Encode()
	if err := p.partC.Request(http.MethodGet, u.String(), nil, nil, headers); err != nil {
		log.Println("part err", err)
		return nil, err
	}

	searchBody := map[string]string{
		"nd":      strconv.FormatInt(time.Now().UnixMilli(), 10),
		"page":    "1",
		"rows":    "10",
		"sidx":    "Item_site",
		"sord":    "asc",
		"_search": "false",
	}
	marshalledSearchBody, _ := json.Marshal(searchBody)
	if err := p.searchC.Request(http.MethodPost, searchURL, bytes.NewReader(marshalledSearchBody), nil, headers); err != nil {
		log.Println("search err", err)
		return nil, err
	}
	if p.searchState.err != nil {
		log.Println("search err", p.searchState.err)
		return nil, p.searchState.err
	}

	detailsBody := map[string]string{
		"partIds": fmt.Sprintf("[%s]", strings.ToUpper(partNumber)),
	}
	marshalledDetailsBody, _ := json.Marshal(detailsBody)
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
