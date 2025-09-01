package aircraftspruce

import (
	"context"
	"errors"
	"fmt"
	"net/url"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/go-rod/rod"
)

func (a AircraftSpruce) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	if err := a.page.Navigate(fmt.Sprintf(searchURL, url.PathEscape(partNumber))); err != nil {
		return nil, err
	}

	var offer dto.Offer

	partNumberEl, err := a.page.MustWaitDOMStable().Sleeper(rod.NotFoundSleeper).Element("div[class=\"prModel\"")
	if err != nil {
		if errors.Is(err, &rod.ElementNotFoundError{}) {
			return nil, nil
		}
		return nil, err
	}
	partNumberText, err := partNumberEl.Text()
	if err != nil {
		return nil, err
	}
	if lines := strings.Split(partNumberText, "\n"); len(lines) > 0 {
		if fields := strings.Fields(lines[len(lines)-1]); len(fields) > 0 {
			offer.PartNumber = fields[len(fields)-1]
		}
	}

	if strings.EqualFold(offer.PartNumber, partNumber) {
		descEl, err := a.page.Element("h2")
		if err != nil {
			return nil, err
		}
		descText, err := descEl.Text()
		if err != nil {
			return nil, err
		}
		offer.Description = strings.TrimSpace(descText)

		priceEl, err := a.page.Element("div[class=\"prPrice\"] div[id=\"np\"]")
		if err != nil {
			return nil, err
		}
		priceText, err := priceEl.Text()
		if err != nil {
			return nil, err
		}
		if parts := strings.Split(priceText, "/"); len(parts) > 0 {
			offer.Price, _ = utils.GetPriceFromString(parts[0])
		}

		return []dto.Offer{offer}, nil
	}
	return nil, nil
}
