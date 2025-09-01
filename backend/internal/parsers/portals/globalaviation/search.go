package globalaviation

import (
	"context"
	"errors"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
)

func (g GlobalAviation) configureSearch() {
	g.javaxSearchC.AllowURLRevisit = true
	g.javaxSearchC.OnHTML(
		"input[name=\"javax.faces.ViewState\"]", func(input *colly.HTMLElement) {
			g.searchState.token = input.Attr("value")
		},
	)
	g.javaxSearchC.OnError(
		func(_ *colly.Response, err error) {
			g.searchState.err = err
		},
	)

	g.updateJavaxSearchC.AllowURLRevisit = true
	g.updateJavaxSearchC.OnRequest(
		func(r *colly.Request) {
			r.Headers.Set("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8")
			r.Headers.Set("Faces-Request", "partial/ajax")
		},
	)
	g.updateJavaxSearchC.OnXML(
		"//update[@id=\"j_id1:javax.faces.ViewState:0\"]", func(update *colly.XMLElement) {
			g.searchState.token = update.Text
		},
	)
	g.updateJavaxSearchC.OnError(
		func(_ *colly.Response, err error) {
			g.searchState.err = err
		},
	)

	g.searchC.AllowURLRevisit = true
	g.searchC.OnRequest(
		func(r *colly.Request) {
			r.Headers.Set("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8")
			r.Headers.Set("Faces-Request", "partial/ajax")
		},
	)
	g.searchC.OnXML(
		"//update[@id=\"gaform:rstable\"]", func(body *colly.XMLElement) {
			bodyHTML, err := goquery.NewDocumentFromReader(strings.NewReader(body.Text))
			if err != nil {
				g.searchState.err = err
				return
			}

			table := bodyHTML.Find("table[id=\"gaform:rstable:0:subrstable\"]")
			table.Find("tbody[id=\"gaform:rstable:0:subrstable:tb\"] > tr").Each(
				func(j int, tr *goquery.Selection) {
					var offer dto.Offer
					tr.Find("td[id*=\"gaform:rstable:0:subrstable\"]").Each(
						func(i int, td *goquery.Selection) {
							text := strings.TrimSpace(td.Text())
							switch i {
							case 1:
								offer.PartNumber = td.Find("a").Text()
							case 2:
								offer.Description = text
							case 3:
								offer.QTY, _ = strconv.Atoi(text)
							case 5:
								offer.Condition = conditions.GetID(text)
							case 8:
								offer.Price, _ = utils.GetPriceFromString(text)
							case 10:
								offer.LeadTime = text
							}
						},
					)
					g.searchState.offers = append(g.searchState.offers, offer)
				},
			)
		},
	)
	g.searchC.OnError(
		func(_ *colly.Response, err error) {
			g.searchState.err = err
		},
	)
}

func (g GlobalAviation) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	defer g.searchState.reset()

	if err := g.javaxSearchC.Visit(searchURL); err != nil {
		return nil, err
	}
	if g.searchState.err != nil {
		return nil, g.searchState.err
	}
	if g.searchState.token == "" {
		return nil, errors.New("token not found")
	}

	if err := g.updateJavaxSearchC.Post(
		searchURL, map[string]string{
			"gaform":                       "gaform",
			"gaform:srch":                  "true",
			"gaform:fpn":                   "",
			"gaform:spn":                   "",
			"gaform:tpn":                   "",
			"gaform:fopn":                  "",
			"gaform:fipn":                  "",
			"gaform:s10area":               partNumber,
			"javax.faces.ViewState":        g.searchState.token,
			"javax.faces.source":           "gaform:j_idt99",
			"javax.faces.partial.event":    "click",
			"javax.faces.partial.execute":  "gaform:j_idt99 @component",
			"javax.faces.partial.render":   "@component",
			"org.richfaces.ajax.component": "gaform:j_idt99",
			"gaform:j_idt99":               "gaform:j_idt99",
			"rfExt":                        "null",
			"AJAX:EVENTS_COUNT":            "1",
			"javax.faces.partial.ajax":     "true",
		},
	); err != nil {
		return nil, err
	}
	if g.searchState.err != nil {
		return nil, g.searchState.err
	}

	if err := g.searchC.Post(
		searchURL, map[string]string{
			"gaform":                       "gaform",
			"gaform:srch":                  "true",
			"gaform:fpn":                   "",
			"gaform:spn":                   "",
			"gaform:tpn":                   "",
			"gaform:fopn":                  "",
			"gaform:fipn":                  "",
			"gaform:s10area":               partNumber,
			"javax.faces.ViewState":        g.searchState.token,
			"javax.faces.source":           "gaform:j_idt105",
			"javax.faces.partial.execute":  "gaform:j_idt105 @component",
			"javax.faces.partial.render":   "@component",
			"org.richfaces.ajax.component": "gaform:j_idt105",
			"gaform:j_idt105":              "gaform:j_idt105",
			"rfExt":                        "null",
			"AJAX:EVENTS_COUNT":            "1",
			"javax.faces.partial.ajax":     "true",
		},
	); err != nil {
		return nil, err
	}
	return g.searchState.offers, g.searchState.err
}
