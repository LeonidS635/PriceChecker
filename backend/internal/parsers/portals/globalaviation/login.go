package globalaviation

import (
	"context"
	"errors"
	"net/http"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/gocolly/colly/v2"
)

func (g GlobalAviation) configureLogin() {
	g.javaxLoginC.AllowURLRevisit = true
	g.javaxLoginC.OnHTML(
		"input[name=\"javax.faces.ViewState\"]", func(input *colly.HTMLElement) {
			g.loginState.token = input.Attr("value")
		},
	)
	g.javaxSearchC.OnError(
		func(_ *colly.Response, err error) {
			g.loginState.err = err
		},
	)

	g.loginC.AllowURLRevisit = true
	g.loginC.SetRedirectHandler(
		func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	)
	g.loginC.OnResponseHeaders(
		func(r *colly.Response) {
			if r != nil && r.StatusCode == http.StatusOK || r.StatusCode == http.StatusFound {
				return
			}
			g.loginState.err = errors.New("invalid credentials")
		},
	)
	g.loginC.OnError(
		func(r *colly.Response, err error) {
			if r != nil && r.StatusCode == http.StatusFound {
				return
			}
			g.loginState.err = err
		},
	)
}

func (g GlobalAviation) Login(ctx context.Context, username string, password string) error {
	if err := g.javaxLoginC.Visit(loginURL); err != nil {
		return err
	}
	if g.loginState.err != nil {
		return g.loginState.err
	}
	if g.loginState.token == "" {
		return errors.New("token not found")
	}

	if err := utils.PostIgnoringStatusCode(
		http.StatusFound, g.loginC, loginURL, map[string]string{
			"login":                        "login",
			"login:username":               username,
			"login:password":               password,
			"javax.faces.ViewState":        g.loginState.token,
			"javax.faces.source":           "login:login",
			"javax.faces.partial.event":    "click",
			"javax.faces.partial.execute":  "login:login @component",
			"javax.faces.partial.render":   "@component",
			"org.richfaces.ajax.component": "login:login",
			"login:login":                  "login:login",
			"rfExt":                        "null",
			"AJAX:EVENTS_COUNT":            "1",
			"javax.faces.partial.ajax":     "true",
		},
	); err != nil {
		return err
	}
	return g.loginState.err
}
