package ajweventory

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type AJWEventory struct {
	searchC     *colly.Collector
	partC       *colly.Collector
	searchState *searchSharedState
}

func NewAJWEventory(baseC *colly.Collector) parsers.Parser {
	a := AJWEventory{
		searchC:     baseC,
		partC:       baseC,
		searchState: newSearchSharedState(),
	}
	a.configureSearch()

	return a
}
