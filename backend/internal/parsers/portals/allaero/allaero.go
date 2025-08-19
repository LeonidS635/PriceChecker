package allaero

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type AllAero struct {
	tokenC  *colly.Collector
	loginC  *colly.Collector
	searchC *colly.Collector

	loginState  *loginSharedState
	searchState *searchSharedState
}

func NewAllAero(baseC *colly.Collector) parsers.Parser {
	a := AllAero{
		tokenC:      baseC,
		loginC:      baseC.Clone(),
		searchC:     baseC.Clone(),
		loginState:  newLoginSharedState(),
		searchState: newSearchSharedState(),
	}
	a.configureLogin()
	a.configureSearch()

	return a
}
