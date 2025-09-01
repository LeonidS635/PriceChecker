package wencor

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type Wencor struct {
	loginURLC   *colly.Collector
	loginC      *colly.Collector
	searchC     *colly.Collector
	detailsC    *colly.Collector
	attributesC *colly.Collector

	loginState  *loginSharedState
	searchState *searchSharedState
}

func NewWencor(baseC *colly.Collector) parsers.Parser {
	w := Wencor{
		loginURLC:   baseC.Clone(),
		loginC:      baseC.Clone(),
		searchC:     baseC.Clone(),
		detailsC:    baseC.Clone(),
		attributesC: baseC.Clone(),
		loginState:  newLoginSharedState(),
		searchState: newSearchSharedState(),
	}
	w.configureLogin()
	w.configureSearch()

	return w
}
