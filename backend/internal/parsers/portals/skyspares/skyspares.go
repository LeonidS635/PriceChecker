package skyspares

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type SkySpares struct {
	searchC  *colly.Collector
	detailsC *colly.Collector

	searchState *searchSharedState
}

func NewSkySpares(baseC *colly.Collector) parsers.Parser {
	s := SkySpares{
		searchC:     baseC,
		detailsC:    baseC.Clone(),
		searchState: newSearchSharedState(),
	}
	s.configureSearch()

	return s
}
