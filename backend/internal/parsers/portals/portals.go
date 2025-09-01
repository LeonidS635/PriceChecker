package portals

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
)

const (
	PortalAerobay domain.PortalID = iota
	PortalAeroSpareParts
	PortalAircraftSpruce
	PortalAirPowerInc
	PortalAJWEventory
	PortalAllAero
	PortalBoeingShop
	PortalDasi
	PortalGlobalAviation
	PortalLASAero
	PortalProponent
	PortalSatAir
	PortalSCross
	PortalSkySpares
	PortalWencor
)

type Portal struct {
	ID   domain.PortalID   `json:"id"`
	Name domain.PortalName `json:"name"`
}

var AllPortals = []Portal{
	{ID: PortalAerobay, Name: "Aerobay"},
	{ID: PortalAeroSpareParts, Name: "AeroSpareParts"},
	{ID: PortalAircraftSpruce, Name: "AircraftSpruce"},
	{ID: PortalAirPowerInc, Name: "AirPowerInc"},
	{ID: PortalAJWEventory, Name: "AJWEventory"},
	{ID: PortalAllAero, Name: "AllAero"},
	{ID: PortalBoeingShop, Name: "BoeingShop"},
	{ID: PortalDasi, Name: "Dasi"},
	{ID: PortalGlobalAviation, Name: "GlobalAviation"},
	{ID: PortalLASAero, Name: "LASAero"},
	//{ID: PortalProponent, Name: "Proponent"},
	{ID: PortalSatAir, Name: "SatAir"},
	{ID: PortalSCross, Name: "SCross"},
	{ID: PortalSkySpares, Name: "SkySpares"},
	{ID: PortalWencor, Name: "Wencor"},
}

var (
	IDByPortalName map[domain.PortalName]domain.PortalID
	PortalNameByID map[domain.PortalID]domain.PortalName
)

func init() {
	IDByPortalName = make(map[domain.PortalName]domain.PortalID)
	PortalNameByID = make(map[domain.PortalID]domain.PortalName)

	for _, portal := range AllPortals {
		IDByPortalName[portal.Name] = portal.ID
		PortalNameByID[portal.ID] = portal.Name
	}
}
