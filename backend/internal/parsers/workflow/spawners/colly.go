package spawners

import (
	"errors"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

var ErrLimitExceeded = errors.New("spawn limit exceeded")

type CollySpawner struct {
	c                 *colly.Collector
	portalConstructor func(c *colly.Collector) parsers.Parser

	spawnedN int
	limit   int
}

func NewCollySpawner(portalConstructor func(c *colly.Collector) parsers.Parser, limit int) spawner {
	return &CollySpawner{
		c:                 colly.NewCollector(),
		portalConstructor: portalConstructor,
		limit:             limit,
	}
}

func (cp *CollySpawner) Spawn() (parsers.Parser, error) {
	if cp.spawnedN > cp.limit {
		return nil, ErrLimitExceeded
	}

	cp.spawnedN++
	return cp.portalConstructor(cp.c.Clone()), nil
}

func (cp *CollySpawner) Limit() int {
	return cp.limit
}
