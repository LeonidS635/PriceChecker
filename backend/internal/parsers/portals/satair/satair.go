package satair

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/gocolly/colly/v2"
)

type SatAir struct {
	loginC       *colly.Collector
	logoutC      *colly.Collector
	offerSearchC *colly.Collector
	addInfoC     *colly.Collector
	plantsC      *colly.Collector

	loginState  *loginSharedState
	searchState *searchSharedState
}

func NewSatAir(baseC *colly.Collector) parsers.Parser {
	s := SatAir{
		loginC:       baseC,
		logoutC:      baseC.Clone(),
		offerSearchC: baseC.Clone(),
		addInfoC:     baseC.Clone(),
		plantsC:      baseC.Clone(),
		loginState:   newLoginSharedState(),
		searchState:  newSearchSharedState(),
	}
	s.configureLogin()
	s.configureLogout()
	s.configureSearch()

	return s
}
