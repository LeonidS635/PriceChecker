package airpowerinc

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
)

const baseURL = "https://www.airpowerinc.com/"

func (a AirPowerInc) configureSearch() {
	a.searchC.AllowURLRevisit = true
	a.attrsC.AllowURLRevisit = true
	a.alternatesC.AllowURLRevisit = true

	a.searchC.OnHTML(
		"body", func(e *colly.HTMLElement) {
			productIDEl := e.DOM.Find("div[class=\"sku\"] span[class=\"value\"]")
			if productIDEl.Length() == 0 {
				return
			}

			idAttr, exists := productIDEl.Attr("id")
			if !exists {
				return
			}
			a.searchState.productID = strings.TrimPrefix(idAttr, "sku-")

			tokenEl := e.DOM.Find("input[name=\"__RequestVerificationToken\"]")
			token, exists := tokenEl.Attr("value")
			if !exists {
				return
			}
			a.searchState.token = token

			e.DOM.Find("dd[id^=\"product_attribute_input\"]").Each(
				func(_ int, s *goquery.Selection) {
					ul := s.Find("ul")
					attrID, exists := ul.Attr("data-attr")
					if !exists {
						return
					}

					li := ul.Find("li").First()
					attrValue, exists := li.Attr("data-attr-value")
					if !exists {
						return
					}

					key := "product_attribute_" + attrID
					a.searchState.attributes[key] = attrValue
				},
			)

			if descEl := e.DOM.Find("h1").First(); descEl.Length() > 0 {
				if parts := strings.SplitN(descEl.Text(), " ", 2); len(parts) > 1 {
					a.searchState.offer.Description = strings.TrimSpace(parts[1])
				}
			}

			if condEl := e.DOM.Find("div[class=\"attributes\"] dd[id^=\"product_attribute_input\"]").First(); condEl.Length() > 0 {
				a.searchState.offer.Condition = conditions.GetID(strings.TrimSpace(condEl.Text()))
			}
		},
	)

	a.attrsC.OnResponse(
		func(r *colly.Response) {
			var jsonResp map[string]any
			if err := json.Unmarshal(r.Body, &jsonResp); err != nil {
				return
			}
			a.searchState.attrsResponse = jsonResp
		},
	)

	a.alternatesC.OnResponse(
		func(r *colly.Response) {
			var alternates []map[string]any
			if err := json.Unmarshal(r.Body, &alternates); err != nil {
				return
			}

			if sku, ok := a.searchState.attrsResponse["sku"].(string); ok {
				a.searchState.offer.PartNumber = sku
			}
			if availability, ok := a.searchState.attrsResponse["stockAvailability"].(string); ok {
				qty, _ := strconv.Atoi(strings.TrimSuffix(strings.TrimSpace(availability), "in stock"))
				a.searchState.offer.QTY = qty
			}
			if price, ok := a.searchState.attrsResponse["priceValue"].(string); ok {
				priceVal, _ := strconv.ParseFloat(strings.TrimPrefix(strings.TrimSpace(price), "$"), 32)
				a.searchState.offer.Price = float32(priceVal)
			}
			if gtin, ok := a.searchState.attrsResponse["gtin"].(string); ok {
				if !strings.Contains(gtin, "|") {
					a.searchState.offer.LeadTime = gtin
				}
			}
			if len(alternates) > 0 {
				for _, alt := range alternates {
					if sku, ok := alt["ProductSku"].(string); ok {
						a.searchState.offer.Interchangeable = append(a.searchState.offer.Interchangeable, sku)
					}
				}
			}
		},
	)

	a.searchC.OnError(
		func(r *colly.Response, err error) {
			a.searchState.err = fmt.Errorf("failed to search: %w", err)
		},
	)
	a.attrsC.OnError(
		func(r *colly.Response, err error) {
			a.searchState.err = fmt.Errorf("failed to get attributes: %w", err)
		},
	)
	a.alternatesC.OnError(
		func(r *colly.Response, err error) {
			a.searchState.err = fmt.Errorf("failed to get alternates: %w", err)
		},
	)
}

func (a AirPowerInc) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer a.searchState.reset()

	if err := a.searchC.Visit(baseURL + url.PathEscape(partNumber)); err != nil {
		return nil, fmt.Errorf("failed to search: %w", err)
	}

	if a.searchState.err != nil {
		return nil, a.searchState.err
	}

	if a.searchState.token == "" {
		return nil, nil
	}

	data := map[string]string{
		"__RequestVerificationToken":                                         a.searchState.token,
		fmt.Sprintf("addtocart_%s.EnteredQuantity", a.searchState.productID): "1",
	}
	for k, v := range a.searchState.attributes {
		data[k] = v
	}

	u, err := url.Parse("https://www.airpowerinc.com/shoppingcart/productdetails_attributechange")
	if err != nil {
		return nil, fmt.Errorf("failed to parse url: %w", err)
	}

	q := u.Query()
	q.Set("productId", a.searchState.productID)
	q.Set("validateAttributeConditions", "false")
	q.Set("loadPicture", "false")
	u.RawQuery = q.Encode()

	if err := a.attrsC.Post(u.String(), data); err != nil {
		return nil, fmt.Errorf("failed to get attributes: %w", err)
	}

	if a.searchState.err != nil {
		return nil, a.searchState.err
	}

	u, err = url.Parse("https://www.airpowerinc.com/AlternateProduct/GetAlternateProducts")
	if err != nil {
		return nil, fmt.Errorf("failed to parse url: %w", err)
	}

	q = u.Query()
	q.Set("productId", a.searchState.productID)
	q.Set("validateAttributeConditions", "false")
	q.Set("loadPicture", "false")
	u.RawQuery = q.Encode()

	data = map[string]string{"id": a.searchState.productID}
	if err := a.alternatesC.Post(u.String(), data); err != nil {
		return nil, fmt.Errorf("failed to get alternates: %w", err)
	}

	return []dto.Offer{a.searchState.offer}, a.searchState.err
}
