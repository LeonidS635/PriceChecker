package aircraftspruce

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type AircraftSpruce struct {
	searchC *colly.Collector

	offers []dto.Offer
	err    error
}

func NewAircraftSpruce(baseC *colly.Collector) parsers.Parser {
	a := &AircraftSpruce{
		searchC: baseC,
	}
	a.configureSearch()

	return a
}
