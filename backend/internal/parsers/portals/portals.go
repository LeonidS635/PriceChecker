package portals

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
)

const (
	Aerobay domain.PortalID = iota
	AeroSpareParts
	AircraftSpruce
	AirPowerInc
	AJWEventory
	AllAero
	BoeingShop
	Dasi
	GlobalAviation
	LASAero
	Proponent
	SatAir
	SCross
	SkySpares
	Wencor
)

type Portal struct {
	ID   domain.PortalID   `json:"id"`
	Name domain.PortalName `json:"name"`
}

var All = []Portal{
	{ID: Aerobay, Name: "Aerobay"},
	{ID: AeroSpareParts, Name: "AeroSpareParts"},
	{ID: AircraftSpruce, Name: "AircraftSpruce"},
	{ID: AirPowerInc, Name: "AirPowerInc"},
	{ID: AJWEventory, Name: "AJWEventory"},
	{ID: AllAero, Name: "AllAero"},
	{ID: BoeingShop, Name: "BoeingShop"},
	{ID: Dasi, Name: "Dasi"},
	{ID: GlobalAviation, Name: "GlobalAviation"},
	{ID: LASAero, Name: "LASAero"},
	{ID: Proponent, Name: "Proponent"},
	{ID: SatAir, Name: "SatAir"},
	{ID: SCross, Name: "SCross"},
	{ID: SkySpares, Name: "SkySpares"},
	{ID: Wencor, Name: "Wencor"},
}

var (
	IDByPortalName map[domain.PortalName]domain.PortalID
	PortalNameByID map[domain.PortalID]domain.PortalName
)

func init() {
	IDByPortalName = make(map[domain.PortalName]domain.PortalID)
	PortalNameByID = make(map[domain.PortalID]domain.PortalName)

	for _, portal := range All {
		IDByPortalName[portal.Name] = portal.ID
		PortalNameByID[portal.ID] = portal.Name
	}
}
