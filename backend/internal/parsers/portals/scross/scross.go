package scross

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type SCross struct {
	searchC     *colly.Collector
	searchState *searchSharedState
}

func NewSCross(baseC *colly.Collector) parsers.Parser {
	s := SCross{
		searchC:     baseC,
		searchState: newSearchSharedState(),
	}
	s.configureSearch()

	return s
}
