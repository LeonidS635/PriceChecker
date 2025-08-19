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
