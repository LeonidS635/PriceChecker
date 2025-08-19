package dto

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
)

type Filter struct {
	PortalIDs  []domain.PortalID `json:"portal_ids"`
	Conditions []conditions.ID   `json:"conditions"`
}
