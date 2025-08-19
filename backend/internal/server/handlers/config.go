package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals"
)

type (
	getPortalsRequest  = struct{}
	getPortalsResponse = struct {
		Portals    []portals.Portal       `json:"portals"`
		Conditions []conditions.Condition `json:"conditions"`
	}
)

func (h Handler) GetConfig(w http.ResponseWriter, r *http.Request) {
	resp := getPortalsResponse{
		Portals:    portals.AllPortals,
		Conditions: conditions.Conditions,
	}

	w.WriteHeader(http.StatusOK)
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		http.Error(w, "Error encoding response: "+err.Error(), http.StatusInternalServerError)
	}
}
