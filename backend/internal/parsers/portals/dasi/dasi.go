package dasi

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type Dasi struct {
	searchC     *colly.Collector
	searchState *searchSharedState
}

func NewDasi(baseC *colly.Collector) parsers.Parser {
	d := Dasi{
		searchC:     baseC,
		searchState: newSearchSharedState(),
	}
	d.configureSearch()

	return d
}
