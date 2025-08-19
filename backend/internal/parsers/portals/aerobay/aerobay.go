package aerobay

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

const (
	baseURL = "https://www.aero-bay.com"
)

type Aerobay struct {
	csrfC   *colly.Collector
	loginC  *colly.Collector
	searchC *colly.Collector

	csrfToken string

	offers []dto.Offer
	err    error
}

func NewAerobayParser(baseC *colly.Collector) parsers.Parser {
	a := &Aerobay{
		csrfC:   baseC,
		loginC:  baseC.Clone(),
		searchC: baseC.Clone(),
	}
	a.configureLogin()
	a.configureSearch()

	return a
}
