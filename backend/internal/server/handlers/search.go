package handlers

import (
	"context"
	"encoding/json"
	"net/http"
	"sync"
	"time"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
)

type (
	searchRequest = struct {
		PartNumbers []string   `json:"part_numbers"`
		Filters     dto.Filter `json:"filters"`
	}
	searchResponse = []offersStatus
)

type offersStatus = struct {
	PortalID            domain.PortalID `json:"portal_id"`
	RequestedPartNumber string          `json:"requested_part_number"`

	Success bool        `json:"success"`
	Offers  []dto.Offer `json:"offers,omitempty"`
	Error   string      `json:"error,omitempty"`
}

func (h Handler) Search(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/x-ndjson")

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
		return
	}
	encoder := json.NewEncoder(w)

	var req searchRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		MustEncodeErrorMsg(w, err, http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithCancel(r.Context())
	defer cancel()

	mu := &sync.Mutex{}
	wg := &sync.WaitGroup{}
	for _, pn := range req.PartNumbers {
		wg.Add(1)
		go func() {
			defer wg.Done()

			reqCtx, reqCtxCancel := context.WithTimeout(ctx, time.Minute)
			defer reqCtxCancel()

			searchResults := h.resProcessor.ProcessSearch(reqCtx, pn, req.Filters)

			var resp searchResponse
			for portalID, res := range searchResults {
				status := offersStatus{
					PortalID:            portalID,
					RequestedPartNumber: pn,
					Success:             res.Err == nil,
					Offers:              res.Offers,
				}
				if res.Err != nil {
					status.Error = res.Err.Error()
				}
				resp = append(resp, status)
			}

			mu.Lock()
			if err := encoder.Encode(resp); err != nil {
				// TODO: what should I do in this case?
			}
			flusher.Flush()
			mu.Unlock()
		}()
	}
	wg.Wait()
}
