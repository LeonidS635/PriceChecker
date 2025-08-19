package models

import (
	"fmt"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type Spawner interface {
	Base() parsers.Authenticator
	Spawn() (parsers.Searcher, error)
}

type CollySpawner struct {
	c                 *colly.Collector
	portalConstructor func(c *colly.Collector) parsers.Parser
}

func NewCollySpawner(portalConstructor func(c *colly.Collector) parsers.Parser) Spawner {
	return &CollySpawner{
		c:                 nil,
		portalConstructor: portalConstructor,
	}
}

func (cp *CollySpawner) Base() parsers.Authenticator {
	cp.c = colly.NewCollector()
	return cp.portalConstructor(cp.c)
}

func (cp *CollySpawner) Spawn() (parsers.Searcher, error) {
	if cp.c == nil {
		return nil, fmt.Errorf("colly spawner: nil base collector (hint: call Base method before Spawn)")
	}
	return cp.portalConstructor(cp.c.Clone()), nil
}
