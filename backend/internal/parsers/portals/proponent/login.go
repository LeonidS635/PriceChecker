package proponent

import (
	"context"
	"errors"
	"net/http"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/gocolly/colly/v2"
)

func (p Proponent) configureLogin() {
	p.viewStateC.AllowURLRevisit = true
	p.viewStateC.OnHTML(
		"input[name=\"__EVENTTARGET\"]", func(input *colly.HTMLElement) {
			p.loginState.eventTarget = input.Attr("value")
		},
	)
	p.viewStateC.OnHTML(
		"input[name=\"__EVENTARGUMENT\"]", func(input *colly.HTMLElement) {
			p.loginState.eventArgument = input.Attr("value")
		},
	)
	p.viewStateC.OnHTML(
		"input[name=\"__EVENTVALIDATION\"]", func(input *colly.HTMLElement) {
			p.loginState.eventValidation = input.Attr("value")
		},
	)
	p.viewStateC.OnHTML(
		"input[name=\"__VIEWSTATE\"]", func(input *colly.HTMLElement) {
			p.loginState.viewState = input.Attr("value")
		},
	)
	p.viewStateC.OnHTML(
		"input[name=\"__VIEWSTATEGENERATOR\"]", func(input *colly.HTMLElement) {
			p.loginState.viewStateGenerator = input.Attr("value")
		},
	)
	p.viewStateC.OnError(
		func(_ *colly.Response, err error) {
			p.loginState.err = err
		},
	)

	p.loginC.AllowURLRevisit = true
	p.loginC.SetRedirectHandler(
		func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	)
	p.loginC.OnResponseHeaders(
		func(r *colly.Response) {
			if r != nil && r.StatusCode == http.StatusFound {
				return
			}
			p.loginState.err = errors.New("invalid credentials")
		},
	)
	p.loginC.OnError(
		func(r *colly.Response, err error) {
			if r != nil && r.StatusCode == http.StatusFound {
				return
			}
			p.loginState.err = err
		},
	)
}

func (p Proponent) Login(ctx context.Context, username string, password string) error {
	headers := http.Header{}
	headers.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

	if err := p.viewStateC.Request(
		http.MethodGet, loginURL, nil, nil, headers); err != nil {
		return err
	}
	if err := utils.PostIgnoringStatusCode(
		http.StatusFound, p.loginC, loginURL, map[string]string{
			"__EVENTTARGET":                 p.loginState.eventTarget,
			"__EVENTARGUMENT":               p.loginState.eventArgument,
			"__EVENTVALIDATION":             p.loginState.eventValidation,
			"__VIEWSTATE":                   p.loginState.viewState,
			"__VIEWSTATEGENERATOR":          p.loginState.viewStateGenerator,
			"ctl00$MainContent$txtUserName": username,
			"ctl00$MainContent$txtPassword": password,
			"ctl00$MainContent$btnLogin":    "Login to Procart",
		},
	); err != nil {
		return err
	}

	_ = p.searchC.SetCookies(searchURL, p.loginC.Cookies(loginURL))
	_ = p.detailsC.SetCookies(detailsURL, p.loginC.Cookies(loginURL))

	return p.loginState.err
}
