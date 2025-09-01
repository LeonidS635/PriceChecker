package proponent

import (
	"context"
	"errors"

	"github.com/gocolly/colly/v2"
)

func (p Proponent) configureLogin() {
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

	p.loginC.OnResponseHeaders(
		func(r *colly.Response) {
			if r.Request.URL.String() == loginURL {
				p.loginState.err = errors.New("invalid credentials")
			}
		},
	)
	p.loginC.OnError(
		func(_ *colly.Response, err error) {
			p.loginState.err = err
		},
	)
}

func (p Proponent) Login(ctx context.Context, username string, password string) error {
	if err := p.viewStateC.Visit(loginURL); err != nil {
		return err
	}
	if err := p.loginC.Post(
		loginURL, map[string]string{
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

	return p.loginState.err
}
