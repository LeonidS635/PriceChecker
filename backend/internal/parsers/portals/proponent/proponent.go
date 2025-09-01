package proponent

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type Proponent struct {
	viewStateC *colly.Collector
	loginC     *colly.Collector
	searchC    *colly.Collector
	partC      *colly.Collector
	detailsC   *colly.Collector

	loginState  *loginSharedState
	searchState *searchSharedState
}

func NewProponent(baseC *colly.Collector) parsers.Parser {
	p := Proponent{
		viewStateC:  baseC.Clone(),
		loginC:      baseC.Clone(),
		searchC:     baseC.Clone(),
		partC:       baseC.Clone(),
		detailsC:    baseC.Clone(),
		loginState:  newLoginSharedState(),
		searchState: newSearchSharedState(),
	}
	p.configureLogin()
	p.configureSearch()

	return p
}
