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
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/boeingshop"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/dasi"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/excel"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/lasaero"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/satair"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/scross"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/skyspares"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners/models"
)

type Spawner interface {
	Base() parsers.Authenticator
	Spawn() (parsers.Searcher, error)
}

var Spawners map[domain.PortalID]Spawner

func init() {
	Spawners = map[domain.PortalID]Spawner{
		portals.PortalAerobay:        models.NewCollySpawner(aerobay.NewAeroBay),
		portals.PortalAircraftSpruce: models.NewCollySpawner(aircraftspruce.NewAircraftSpruce),
		portals.PortalAirPowerInc:    models.NewCollySpawner(airpowerinc.NewAirPowerInc),
		portals.PortalAJWEventory:    models.NewCollySpawner(ajweventory.NewAJWEventory),
		portals.PortalAllAero:        models.NewCollySpawner(allaero.NewAllAero),
		portals.PortalBoeingShop:     models.NewCollySpawner(boeingshop.NewBoeingShop),
		portals.PortalDasi:           models.NewCollySpawner(dasi.NewDasi),
		portals.PortalLASAero:        models.NewCollySpawner(lasaero.NewLASAero),
		portals.PortalSatAir:         models.NewCollySpawner(satair.NewSatAir),
		portals.PortalSCross:         models.NewCollySpawner(scross.NewSCross),
		portals.PortalSkySpares:      models.NewCollySpawner(skyspares.NewSkySpares),
	}
}

func RegisterExcelSpawner(path string) domain.PortalID {
	fileID := domain.PortalID(len(Spawners) + 1)
	Spawners[fileID] = models.NewExcelSpawner(excel.NewExcelParser, path)
	credentials.Credentials[fileID] = dto.Credentials{} // TODO: temporary fix
	return fileID
}
