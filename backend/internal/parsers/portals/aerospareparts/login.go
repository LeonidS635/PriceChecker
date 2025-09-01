package aerospareparts

import (
	"context"
	"errors"

	"github.com/gocolly/colly/v2"
)

func (a AeroSpareParts) configureLogin() {
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

	a.loginC.OnHTML(
		"div[class=\"validation-summary-errors text-danger\"]", func(_ *colly.HTMLElement) {
			a.loginState.err = errors.New("invalid credentials")
		},
	)
	a.loginC.OnError(
		func(_ *colly.Response, err error) {
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

	if err := a.loginC.Post(
		loginURL, map[string]string{
			"__RequestVerificationToken": a.loginState.token,
			"UserName":                   username,
			"Password":                   password,
		},
	); err != nil {
		return err
	}
	return a.loginState.err
}
