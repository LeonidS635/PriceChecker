package spawners

import (
	"sync"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
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
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/lasaero"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/proponent"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/satair"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/scross"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/skyspares"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/wencor"
	"github.com/go-rod/rod"
	"github.com/go-rod/rod/lib/launcher"
)

type spawner interface {
	Spawn() (parsers.Parser, error)
	Limit() int
}

var Spawners map[domain.PortalID]spawner

var lastFreeID domain.PortalID // Temp: risk of overflow --> needed another system

const defaultLimit = 25

func init() {
	path, _ := launcher.LookPath()
	u := launcher.New().Bin(path).MustLaunch()
	browser := rod.New().ControlURL(u).MustConnect().NoDefaultDevice()

	Spawners = map[domain.PortalID]spawner{
		portals.Aerobay:        NewCollySpawner(aerobay.NewAeroBay, defaultLimit),
		portals.AeroSpareParts: NewCollySpawner(aerospareparts.NewAeroSpareParts, defaultLimit),
		portals.AircraftSpruce: NewRodSpawner(browser, aircraftspruce.NewAircraftSpruce, defaultLimit),
		portals.AirPowerInc:    NewCollySpawner(airpowerinc.NewAirPowerInc, defaultLimit),
		portals.AJWEventory:    NewCollySpawner(ajweventory.NewAJWEventory, defaultLimit),
		portals.AllAero:        NewCollySpawner(allaero.NewAllAero, defaultLimit),
		portals.BoeingShop:     NewCollySpawner(boeingshop.NewBoeingShop, defaultLimit),
		portals.Dasi:           NewCollySpawner(dasi.NewDasi, defaultLimit),
		portals.LASAero:        NewCollySpawner(lasaero.NewLASAero, defaultLimit),
		portals.Proponent:      NewCollySpawner(proponent.NewProponent, 1),
		portals.SatAir:         NewCollySpawner(satair.NewSatAir, defaultLimit),
		portals.SCross:         NewCollySpawner(scross.NewSCross, defaultLimit),
		portals.SkySpares:      NewCollySpawner(skyspares.NewSkySpares, defaultLimit),
		portals.Wencor:         NewCollySpawner(wencor.NewWencor, defaultLimit),
	}
	lastFreeID = domain.PortalID(len(Spawners))
}

type excelFilesManager struct {
	mu      *sync.Mutex
	fileIDs map[string]domain.PortalID
}

func (e excelFilesManager) getID(path string) (domain.PortalID, bool) {
	e.mu.Lock()
	defer e.mu.Unlock()

	id, ok := e.fileIDs[path]
	return id, ok
}

func (e excelFilesManager) save(path string) domain.PortalID {
	e.mu.Lock()
	defer e.mu.Unlock()

	fileID := lastFreeID
	lastFreeID++

	e.fileIDs[path] = fileID
	return fileID
}

var e = excelFilesManager{mu: &sync.Mutex{}, fileIDs: make(map[string]domain.PortalID)}

func RegisterExcelSpawner(path string) (domain.PortalID, spawner) {
	id, ok := e.getID(path)
	if !ok {
		id = e.save(path)
	}

	return id, NewExcelSpawner(excel.NewExcelParser, path, 1)
}
