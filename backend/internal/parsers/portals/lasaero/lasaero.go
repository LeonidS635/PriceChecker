package lasaero

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type LASAero struct {
	tokenC  *colly.Collector
	loginC  *colly.Collector
	searchC *colly.Collector

	loginState  *loginSharedState
	searchState *searchSharedState
}

func NewLASAero(baseC *colly.Collector) parsers.Parser {
	l := LASAero{
		tokenC:      baseC,
		loginC:      baseC.Clone(),
		searchC:     baseC.Clone(),
		loginState:  newLoginSharedState(),
		searchState: newSearchSharedState(),
	}
	l.configureLogin()
	l.configureSearch()

	return l
}
