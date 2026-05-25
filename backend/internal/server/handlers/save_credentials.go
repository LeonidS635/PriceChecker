package handlers

import (
	"context"
	"encoding/json"
	"net/http"
	"time"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
)

type (
	saveCredentialsRequest = []struct {
		PortalID domain.PortalID `json:"portal_id"`
		dto.Credentials
	}
	saveCredentialsResponse = []portalStatus
)

func (h Handler) SaveCredentials(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	var req saveCredentialsRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		MustEncodeErrorMsg(w, err, http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()

	creds := make(map[domain.PortalID]dto.Credentials, len(req))
	for _, c := range req {
		creds[c.PortalID] = c.Credentials
	}
	saveCredentialsResults := h.resProcessor.ProcessSaveCredentials(ctx, creds)

	var resp saveCredentialsResponse
	for portalID, err := range saveCredentialsResults {
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
