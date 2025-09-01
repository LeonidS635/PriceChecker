package models

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/go-rod/rod"
)

type RodSpawner struct {
	browser           *rod.Browser
	portalConstructor func(page *rod.Page) parsers.Parser
}

func NewRodSpawner(browser *rod.Browser, portalConstructor func(page *rod.Page) parsers.Parser) Spawner {
	return RodSpawner{
		browser:           browser.MustIncognito(),
		portalConstructor: portalConstructor,
	}
}

func (r RodSpawner) Base() parsers.Authenticator {
	return r.portalConstructor(r.browser.MustPage())
}

func (r RodSpawner) Spawn() (parsers.Searcher, error) {
	return r.portalConstructor(r.browser.MustPage()), nil
}
