package boeingshop

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type BoeingShop struct {
	searchC     *colly.Collector
	searchState *searchSharedState
}

func NewBoeingShop(baseC *colly.Collector) parsers.Parser {
	b := BoeingShop{
		searchC:     baseC,
		searchState: newSearchSharedState(),
	}
	b.configureSearch()

	return b
}
