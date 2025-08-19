package airpowerinc

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type AirPowerInc struct {
	searchC     *colly.Collector
	attrsC      *colly.Collector
	alternatesC *colly.Collector

	searchState *searchSharedState
}

func NewAirPowerInc(baseC *colly.Collector) parsers.Parser {
	a := AirPowerInc{
		searchC:     baseC,
		attrsC:      baseC.Clone(),
		alternatesC: baseC.Clone(),
		searchState: newSearchSharedState(),
	}
	a.configureSearch()

	return a
}
