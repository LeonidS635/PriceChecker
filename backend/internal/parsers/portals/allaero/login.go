package allaero

import (
	"context"
	"fmt"
	"net/url"

	"github.com/gocolly/colly/v2"
)

// TODO: this site uses reCAPTCHA, maybe I need another way to parse (rod)

func (a AllAero) configureLogin() {
	a.tokenC.OnHTML(
		"input[name=\"__RequestVerificationToken\"]", func(e *colly.HTMLElement) {
			a.loginState.token = e.Attr("value")
		},
	)
	a.tokenC.OnError(
		func(r *colly.Response, err error) {
			a.loginState.err = err
		},
	)

	a.loginC.OnResponseHeaders(
		func(r *colly.Response) {
			//log.Println(r.Request.URL.String())
		},
	)
	a.loginC.OnError(
		func(r *colly.Response, err error) {
			a.loginState.err = err
		},
	)
}

func (a AllAero) Login(ctx context.Context, username string, password string) error {
	if err := a.tokenC.Visit(loginURL); err != nil {
		return err
	}
	if a.loginState.err != nil {
		return a.loginState.err
	}
	if a.loginState.token == "" {
		return fmt.Errorf("no token found")
	}

	u, _ := url.Parse(loginURL)
	q := u.Query()
	q.Set("handler", "json-signin")
	u.RawQuery = q.Encode()

	data := map[string]string{
		"SignInAttempt.EmailAddress": username,
		"SignInAttempt.Password":     password,
		"__RequestVerificationToken": a.loginState.token,
	}
	if err := a.loginC.Post(u.String(), data); err != nil {
		return err
	}

	return a.loginState.err
}
