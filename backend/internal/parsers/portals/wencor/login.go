package wencor

import (
	"context"
	"errors"
	"net/http"
	"regexp"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/gocolly/colly/v2"
)

func (w Wencor) configureLogin() {
	w.loginURLC.AllowURLRevisit = true
	w.loginURLC.OnHTML(
		"div[class=\"rhy widget__rhythmloginmultiinstancesportlet_WAR_rhythmloginmultiinstancesportlet_INSTANCE_Al8rQt3TrPh8_\"] ~ script",
		func(script *colly.HTMLElement) {
			re := regexp.MustCompile(`actionURL:\s*'([^']+)'`)
			match := re.FindStringSubmatch(script.Text)
			if len(match) > 1 {
				w.loginState.loginURL = strings.ReplaceAll(match[1], `\/`, `/`)
			} else {
				w.loginState.err = errors.New("login URL not found")
			}
		},
	)
	w.loginURLC.OnError(
		func(_ *colly.Response, err error) {
			w.loginState.err = err
		},
	)

	w.loginC.AllowURLRevisit = true
	w.loginC.SetRedirectHandler(
		func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	)
	w.loginC.OnResponseHeaders(
		func(r *colly.Response) {
			if r != nil && r.StatusCode == http.StatusFound {
				return
			}
			w.loginState.err = errors.New("invalid credential")
		},
	)
	w.loginC.OnError(
		func(r *colly.Response, err error) {
			if r != nil && r.StatusCode == http.StatusFound {
				return
			}
			w.loginState.err = err
		},
	)
}

func (w Wencor) Login(ctx context.Context, username string, password string) error {
	if err := w.loginURLC.Visit(loginURL); err != nil {
		return err
	}
	if w.loginState.err != nil {
		return w.loginState.err
	}

	if err := utils.PostIgnoringStatusCode(
		http.StatusFound, w.loginC, w.loginState.loginURL, map[string]string{
			"redirect": "",
			"_rhythmloginmultiinstancesportlet_WAR_rhythmloginmultiinstancesportlet_INSTANCE_Al8rQt3TrPh8_login":    username,
			"_rhythmloginmultiinstancesportlet_WAR_rhythmloginmultiinstancesportlet_INSTANCE_Al8rQt3TrPh8_password": password,
		},
	); err != nil {
		return err
	}
	return w.loginState.err
}
