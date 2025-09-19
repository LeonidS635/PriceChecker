package spawners

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/go-rod/rod"
	"github.com/go-rod/rod/lib/proto"
)

type RodSpawner struct {
	browser           *rod.Browser
	portalConstructor func(page *rod.Page) parsers.Parser

	spawnedN int
	limit    int
}

func NewRodSpawner(browser *rod.Browser, portalConstructor func(page *rod.Page) parsers.Parser, limit int) spawner {
	return &RodSpawner{
		browser:           browser.MustIncognito(),
		portalConstructor: portalConstructor,
		limit:             limit,
	}
}

func (r *RodSpawner) Spawn() (parsers.Parser, error) {
	if r.spawnedN > r.limit {
		return nil, ErrLimitExceeded
	}

	page, err := r.browser.Page(proto.TargetCreateTarget{})
	if err != nil {
		return nil, err
	}

	r.spawnedN++
	return r.portalConstructor(page), nil
}

func (r *RodSpawner) Limit() int {
	return r.limit
}
