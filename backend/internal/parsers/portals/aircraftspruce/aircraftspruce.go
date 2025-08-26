package aircraftspruce

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type AircraftSpruce struct {
	searchC     *colly.Collector
	searchState *searchSharedState
}

func NewAircraftSpruce(baseC *colly.Collector) parsers.Parser {
	a := &AircraftSpruce{
		searchC:     baseC,
		searchState: newSearchSharedState(),
	}
	a.configureSearch()

	return a
}
