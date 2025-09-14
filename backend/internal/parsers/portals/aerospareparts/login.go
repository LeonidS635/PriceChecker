package aerospareparts

import (
	"context"
	"errors"
	"net/http"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/gocolly/colly/v2"
)

func (a AeroSpareParts) configureLogin() {
	a.tokenC.AllowURLRevisit = true
	a.tokenC.OnHTML(
		"input[name=\"__RequestVerificationToken\"]", func(e *colly.HTMLElement) {
			a.loginState.token = e.Attr("value")
		},
	)
	a.tokenC.OnError(
		func(_ *colly.Response, err error) {
			a.loginState.err = err
		},
	)

	a.loginC.AllowURLRevisit = true
	a.loginC.SetRedirectHandler(
		func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	)
	a.loginC.OnResponseHeaders(
		func(r *colly.Response) {
			if r == nil || r.StatusCode != http.StatusFound {
				a.loginState.err = errors.New("invalid credentials")
			}
		},
	)
	a.loginC.OnError(
		func(r *colly.Response, err error) {
			if r != nil && r.StatusCode == http.StatusFound {
				return
			}
			a.loginState.err = err
		},
	)
}

func (a AeroSpareParts) Login(ctx context.Context, username string, password string) error {
	if err := a.tokenC.Visit(loginURL); err != nil {
		return err
	}
	if a.loginState.err != nil {
		return a.loginState.err
	}
	if a.loginState.token == "" {
		return errors.New("no token found")
	}

	if err := utils.PostIgnoringStatusCode(
		http.StatusFound, a.loginC, loginURL, map[string]string{
			"__RequestVerificationToken": a.loginState.token,
			"UserName":                   username,
			"Password":                   password,
		},
	); err != nil {
		return err
	}
	return a.loginState.err
}
