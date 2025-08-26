package aerobay

import (
	"context"
	"fmt"

	"github.com/gocolly/colly/v2"
)

func (a *AeroBay) configureLogin() {
	a.tokenC.OnHTML(
		"input[name=\"_csrf\"]", func(e *colly.HTMLElement) {
			a.loginState.token = e.Attr("value")
		},
	)
	a.tokenC.OnError(
		func(_ *colly.Response, err error) {
			a.loginState.err = err
		},
	)

	a.loginC.OnResponseHeaders(
		func(r *colly.Response) {
			if r.Request.URL.String() == loginURL {
				a.loginState.err = fmt.Errorf("failed to login: incorrect username and/or password")
			}
		},
	)
	a.loginC.OnError(
		func(_ *colly.Response, err error) {
			a.loginState.err = err
		},
	)
}

func (a *AeroBay) Login(ctx context.Context, username, password string) error {
	if err := a.tokenC.Visit(baseURL); err != nil {
		return err
	}
	if a.loginState.err != nil {
		return a.loginState.err
	}
	if a.loginState.token == "" {
		return fmt.Errorf("csrf token not found")
	}

	if err := a.loginC.Post(
		loginURL, map[string]string{
			"_csrf":    a.loginState.token,
			"userName": username,
			"password": password,
		},
	); err != nil {
		return err
	}

	return a.loginState.err
}
