package portals

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
)

const (
	PortalAerobay domain.PortalID = iota
	PortalAircraftSpruce
	PortalAirPowerInc
	PortalAJWEventory
	PortalAllAero
	PortalBoeingShop
	PortalDasi
	PortalLASAero
	PortalSatAir
	PortalSCross
	PortalSkySpares
)

type Portal struct {
	ID   domain.PortalID   `json:"id"`
	Name domain.PortalName `json:"name"`
}

var AllPortals = []Portal{
	{ID: PortalAerobay, Name: "Aerobay"},
	{ID: PortalAircraftSpruce, Name: "AircraftSpruce"},
	{ID: PortalAirPowerInc, Name: "AirPowerInc"},
	{ID: PortalAJWEventory, Name: "AJWEventory"},
	{ID: PortalAllAero, Name: "AllAero"},
	{ID: PortalBoeingShop, Name: "BoeingShop"},
	{ID: PortalDasi, Name: "Dasi"},
	{ID: PortalLASAero, Name: "LASAero"},
	{ID: PortalSatAir, Name: "SatAir"},
	{ID: PortalSCross, Name: "SCross"},
	{ID: PortalSkySpares, Name: "SkySpares"},
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
