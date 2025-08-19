package aerobay

import (
	"context"
	"fmt"

	"github.com/gocolly/colly/v2"
)

const loginURL = "https://www.aero-bay.com/j_spring_security_check"

func (a *Aerobay) configureLogin() {
	a.csrfC.OnHTML(
		"input[name=\"_csrf\"]", func(e *colly.HTMLElement) {
			a.csrfToken = e.Attr("value")
		},
	)

	a.loginC.OnResponseHeaders(
		func(r *colly.Response) {
			if r.Request.URL.String() == loginURL {
				a.err = fmt.Errorf("failed to login: incorrect username and/or password")
			}
		},
	)

	a.csrfC.OnError(
		func(_ *colly.Response, err error) {
			a.err = err
		},
	)
	a.loginC.OnError(
		func(_ *colly.Response, err error) {
			a.err = err
		},
	)
}

func (a *Aerobay) Login(ctx context.Context, username, password string) error {
	if err := a.csrfC.Visit(baseURL); err != nil {
		return err
	}
	if a.csrfToken == "" {
		return fmt.Errorf("csrf token not found")
	}

	if err := a.loginC.Post(
		loginURL, map[string]string{
			"_csrf":    a.csrfToken,
			"userName": username,
			"password": password,
		},
	); err != nil {
		return err
	}

	return nil
}
