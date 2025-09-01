package spawners

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/credentials"
	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/aerobay"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/aerospareparts"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/aircraftspruce"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/airpowerinc"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/ajweventory"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/allaero"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/boeingshop"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/dasi"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/excel"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/globalaviation"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/lasaero"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/satair"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/scross"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/skyspares"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/wencor"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners/models"
	"github.com/go-rod/rod"
	"github.com/go-rod/rod/lib/launcher"
)

const defaultRateLimit = 4

type Spawner interface {
	Base() parsers.Authenticator
	Spawn() (parsers.Searcher, error)
	GetRateLimit() int
}

var Spawners map[domain.PortalID]Spawner

func init() {
	path, _ := launcher.LookPath()
	u := launcher.New().Bin(path).MustLaunch()
	browser := rod.New().ControlURL(u).MustConnect().NoDefaultDevice()

	Spawners = map[domain.PortalID]Spawner{
		portals.PortalAerobay:        models.NewCollySpawner(aerobay.NewAeroBay, defaultRateLimit),
		portals.PortalAeroSpareParts: models.NewCollySpawner(aerospareparts.NewAeroSpareParts, defaultRateLimit),
		portals.PortalAircraftSpruce: models.NewRodSpawner(browser, aircraftspruce.NewAircraftSpruce, defaultRateLimit),
		portals.PortalAirPowerInc:    models.NewCollySpawner(airpowerinc.NewAirPowerInc, defaultRateLimit),
		portals.PortalAJWEventory:    models.NewCollySpawner(ajweventory.NewAJWEventory, defaultRateLimit),
		portals.PortalAllAero:        models.NewCollySpawner(allaero.NewAllAero, defaultRateLimit),
		portals.PortalBoeingShop:     models.NewCollySpawner(boeingshop.NewBoeingShop, defaultRateLimit),
		portals.PortalDasi:           models.NewCollySpawner(dasi.NewDasi, defaultRateLimit),
		portals.PortalGlobalAviation: models.NewCollySpawner(globalaviation.NewGlobalAviation, 1),
		portals.PortalLASAero:        models.NewCollySpawner(lasaero.NewLASAero, defaultRateLimit),
		//portals.PortalProponent:      models.NewCollySpawner(proponent.NewProponent),
		portals.PortalSatAir:    models.NewCollySpawner(satair.NewSatAir, defaultRateLimit),
		portals.PortalSCross:    models.NewCollySpawner(scross.NewSCross, defaultRateLimit),
		portals.PortalSkySpares: models.NewCollySpawner(skyspares.NewSkySpares, defaultRateLimit),
		portals.PortalWencor:    models.NewCollySpawner(wencor.NewWencor, defaultRateLimit),
	}
}

func RegisterExcelSpawner(path string) domain.PortalID {
	fileID := domain.PortalID(len(Spawners) + 1)
	Spawners[fileID] = models.NewExcelSpawner(excel.NewExcelParser, path)
	credentials.Credentials[fileID] = dto.Credentials{} // TODO: temporary fix
	return fileID
}
