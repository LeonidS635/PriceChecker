package aircraftspruce

import (
	"time"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/go-rod/rod"
)

type AircraftSpruce struct {
	page *rod.Page
}

func NewAircraftSpruce(page *rod.Page) parsers.Parser {
	return AircraftSpruce{page: page.Timeout(20 * time.Second)}
}
