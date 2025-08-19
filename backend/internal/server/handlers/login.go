package handlers

import (
	"context"
	"encoding/json"
	"net/http"
	"time"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
)

type (
	loginRequest = []struct {
		PortalID domain.PortalID `json:"portal_id"`
		Username string          `json:"username"`
		Password string          `json:"password"`
	}
	loginResponse = []portalStatus
)

type portalStatus = struct {
	PortalID domain.PortalID `json:"portal_id"`
	Success  bool            `json:"success"`
	Error    string          `json:"error,omitempty"`
}

func (h Handler) Login(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	var req loginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		MustEncodeErrorMsg(w, err, http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()

	portalIDs := make([]domain.PortalID, 0, len(req))
	for _, p := range req {
		portalIDs = append(portalIDs, p.PortalID)
	}
	loginResults := h.resProcessor.ProcessLogin(ctx, portalIDs)

	var resp loginResponse
	for portalID, err := range loginResults {
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
