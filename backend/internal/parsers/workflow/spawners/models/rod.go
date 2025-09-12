package models

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/go-rod/rod"
)

type RodSpawner struct {
	browser           *rod.Browser
	portalConstructor func(page *rod.Page) parsers.Parser

	count int
	limit int
}

func NewRodSpawner(browser *rod.Browser, portalConstructor func(page *rod.Page) parsers.Parser, limit int) Spawner {
	return RodSpawner{
		browser:           browser.MustIncognito(),
		portalConstructor: portalConstructor,
		limit:             limit,
	}
}

func (r RodSpawner) Base() parsers.Authenticator {
	r.count++
	return r.portalConstructor(r.browser.MustPage())
}

func (r RodSpawner) Spawn() (parsers.Parser, error) {
	if r.count > r.limit {
		return nil, ErrRateLimitExceeded
	}

	r.count++
	return r.portalConstructor(r.browser.MustPage()), nil
}

func (r RodSpawner) GetRateLimit() int {
	return r.limit
}
