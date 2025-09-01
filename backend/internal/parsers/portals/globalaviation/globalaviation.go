package globalaviation

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type GlobalAviation struct {
	javaxLoginC        *colly.Collector
	loginC             *colly.Collector
	javaxSearchC       *colly.Collector
	updateJavaxSearchC *colly.Collector
	searchC            *colly.Collector

	loginState  *loginSharedState
	searchState *searchSharedState
}

func NewGlobalAviation(baseC *colly.Collector) parsers.Parser {
	g := GlobalAviation{
		javaxLoginC:        baseC.Clone(),
		loginC:             baseC.Clone(),
		javaxSearchC:       baseC.Clone(),
		updateJavaxSearchC: baseC.Clone(),
		searchC:            baseC.Clone(),
		loginState:         newLoginSharedState(),
		searchState:        newSearchSharedState(),
	}
	g.configureLogin()
	g.configureSearch()

	return g
}
