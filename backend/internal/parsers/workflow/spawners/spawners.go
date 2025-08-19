package spawners

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/credentials"
	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/aerobay"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/aircraftspruce"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/airpowerinc"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/ajweventory"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/allaero"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/excel"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners/models"
)

type Spawner interface {
	Base() parsers.Authenticator
	Spawn() (parsers.Searcher, error)
}

var Spawners map[domain.PortalID]Spawner

func init() {
	Spawners = map[domain.PortalID]Spawner{
		portals.PortalAerobay:        models.NewCollySpawner(aerobay.NewAerobayParser),
		portals.PortalAircraftSpruce: models.NewCollySpawner(aircraftspruce.NewAircraftSpruce),
		portals.PortalAirPowerInc:    models.NewCollySpawner(airpowerinc.NewAirPowerInc),
		portals.PortalAJWEventory:    models.NewCollySpawner(ajweventory.NewAJWEventory),
		portals.PortalAllAero:        models.NewCollySpawner(allaero.NewAllAero),
	}
}

func RegisterExcelSpawner(path string) domain.PortalID {
	fileID := domain.PortalID(len(Spawners) + 1)
	Spawners[fileID] = models.NewExcelSpawner(excel.NewExcelParser, path)
	credentials.Credentials[fileID] = dto.Credentials{} // TODO: temporary fix
	return fileID
}
