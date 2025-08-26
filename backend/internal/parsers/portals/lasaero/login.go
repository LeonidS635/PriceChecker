package lasaero

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"

	"github.com/gocolly/colly/v2"
)

func (l LASAero) configureLogin() {
	l.tokenC.OnHTML(
		"input[name=\"csrfmiddlewaretoken\"]", func(e *colly.HTMLElement) {
			l.loginState.token = e.Attr("value")
		},
	)
	l.tokenC.OnError(
		func(_ *colly.Response, err error) {
			l.loginState.err = err
		},
	)

	l.loginC.OnRequest(
		func(r *colly.Request) {
			r.Headers.Set("Referer", "https://www.lasaero.com/account")
			r.Headers.Set(
				"User-Agent",
				"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
			)
			r.Headers.Set("X-Requested-With", "XMLHttpRequest")
		},
	)
	l.loginC.OnResponse(
		func(r *colly.Response) {
			type response struct {
				Status  int `json:"status"`
				Content struct {
					Visibility struct {
						LoginSuccess bool `json:".ajxobj_show_on_login_success"`
					} `json:"visibility"`
				} `json:"content"`
			}
			resp := response{}

			if err := json.Unmarshal(r.Body, &resp); err != nil {
				l.loginState.err = err
				return
			}

			if resp.Status != http.StatusOK || !resp.Content.Visibility.LoginSuccess {
				l.loginState.err = errors.New("invalid credentials")
			}
		},
	)
	l.loginC.OnError(
		func(_ *colly.Response, err error) {
			l.loginState.err = err
		},
	)
}

func (l LASAero) Login(ctx context.Context, username string, password string) error {
	if err := l.tokenC.Visit(accountURL); err != nil {
		return err
	}
	if l.loginState.err != nil {
		return l.loginState.err
	}
	if l.loginState.token == "" {
		return errors.New("no CSRF token found")
	}

	if err := l.loginC.Post(
		loginURL, map[string]string{
			"csrfmiddlewaretoken": l.loginState.token,
			"shopper_email":       username,
			"shopper_pass":        password,
		},
	); err != nil {
		return err
	}
	return l.loginState.err
}
