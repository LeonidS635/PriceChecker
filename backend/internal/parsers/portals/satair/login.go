package satair

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"

	"github.com/gocolly/colly/v2"
)

func (s SatAir) configureLogin() {
	s.loginC.AllowURLRevisit = true
	s.loginC.OnResponse(
		func(r *colly.Response) {
			if err := json.Unmarshal(r.Body, &s.loginState.loginResponse); err != nil {
				s.loginState.err = err
				return
			}
		},
	)
	s.loginC.OnError(
		func(r *colly.Response, err error) {
			if r.StatusCode == http.StatusBadRequest {
				err = errors.New("invalid credentials")
			}
			s.loginState.err = err
		},
	)
}

func (s SatAir) Login(ctx context.Context, username string, password string) error {
	if err := s.loginC.Post(
		loginURL, map[string]string{
			"userId":     username,
			"password":   password,
			"rememberMe": "true",
		},
	); err != nil {
		return err
	}
	if s.loginState.err != nil {
		return s.loginState.err
	}

	_ = s.addInfoC.SetCookies(addInfoURL, s.loginC.Cookies(loginURL))
	_ = s.plantsC.SetCookies(plantsURL, s.loginC.Cookies(loginURL))

	return nil
}
