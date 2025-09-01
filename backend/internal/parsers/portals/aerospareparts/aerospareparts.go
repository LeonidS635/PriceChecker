package aerospareparts

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type AeroSpareParts struct {
	tokenC   *colly.Collector
	loginC   *colly.Collector
	searchC  *colly.Collector
	detailsC *colly.Collector
	quoteC   *colly.Collector

	loginState  *loginSharedState
	searchState *searchSharedState
}

func NewAeroSpareParts(baseC *colly.Collector) parsers.Parser {
	a := AeroSpareParts{
		tokenC:      baseC,
		loginC:      baseC.Clone(),
		searchC:     baseC.Clone(),
		detailsC:    baseC.Clone(),
		quoteC:      baseC.Clone(),
		loginState:  newLoginSharedState(),
		searchState: newSearchSharedState(),
	}
	a.configureLogin()
	a.configureSearch()

	return a
}
