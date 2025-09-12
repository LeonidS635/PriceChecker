package handlers

import (
	"context"
	"encoding/json"
	"net/http"
	"time"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
)

type (
	logoutRequest = struct {
		PortalIDs []domain.PortalID `json:"portal_ids"`
	}
	logoutResponse = []portalStatus
)

func (h Handler) Logout(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	var req logoutRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		MustEncodeErrorMsg(w, err, http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()

	logoutResults := h.resProcessor.ProcessLogout(ctx, req.PortalIDs)

	var resp logoutResponse
	for portalID, err := range logoutResults {
		status := portalStatus{
			PortalID: portalID,
			Success:  err == nil,
		}
		if err != nil {
			status.Error = err.Error()
		}
		resp = append(resp, status)
	}

	w.WriteHeader(http.StatusOK)
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		MustEncodeErrorMsg(w, err, http.StatusInternalServerError)
	}
}
