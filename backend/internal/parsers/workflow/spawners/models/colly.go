package models

import (
	"errors"
	"fmt"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

var ErrRateLimitExceeded = errors.New("rate limit exceeded")

type Spawner interface {
	Base() parsers.Authenticator
	Spawn() (parsers.Parser, error)
	GetRateLimit() int
}

type CollySpawner struct {
	c                 *colly.Collector
	portalConstructor func(c *colly.Collector) parsers.Parser

	count int
	limit int
}

func NewCollySpawner(portalConstructor func(c *colly.Collector) parsers.Parser, limit int) Spawner {
	return &CollySpawner{
		c:                 colly.NewCollector(),
		portalConstructor: portalConstructor,
		limit:             limit,
	}
}

func (cp *CollySpawner) Base() parsers.Authenticator {
	cp.count = 0 // Temp fix

	//cp.c = colly.NewCollector()
	return cp.portalConstructor(cp.c)
}

func (cp *CollySpawner) Spawn() (parsers.Parser, error) {
	if cp.c == nil {
		return nil, fmt.Errorf("colly spawner: nil base collector (hint: call Base method before Spawn)")
	}
	if cp.count > cp.limit {
		return nil, ErrRateLimitExceeded
	}

	cp.count++
	return cp.portalConstructor(cp.c.Clone()), nil
}

func (cp *CollySpawner) GetRateLimit() int {
	return cp.limit
}
