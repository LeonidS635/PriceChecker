package api

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"strconv"
	"time"

	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/api/dto"
	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/service"
	"github.com/google/uuid"
)

type rfqService interface {
	GetClientRFQs(ctx context.Context, clientID uint64, after *domain.Cursor, limit int) (domain.RFQPage, error)
}

type Handler struct {
	service rfqService
}

func NewHandler(service rfqService) *Handler {
	return &Handler{service: service}
}

func (h *Handler) GetClientRFQs(w http.ResponseWriter, r *http.Request) {
	clientID, err := strconv.ParseUint(r.PathValue("clientID"), 10, 64)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid client_id")
		return
	}

	after, err := parseCursor(r)
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	limit, err := parseQueryInt(r, "limit", service.DefaultLimit)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid limit")
		return
	}

	page, err := h.service.GetClientRFQs(r.Context(), clientID, after, limit)
	if err != nil {
		slog.Error("failed to get client rfqs", "client_id", clientID, "err", err)
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}

	writeJSON(w, http.StatusOK, dto.FromDomainPage(page, clientNames[clientID]))
}

func parseCursor(r *http.Request) (*domain.Cursor, error) {
	jobIDRaw := r.URL.Query().Get("after_job_id")
	receivedAtRaw := r.URL.Query().Get("after_received_at")

	if jobIDRaw == "" && receivedAtRaw == "" {
		return nil, nil
	}
	if jobIDRaw == "" || receivedAtRaw == "" {
		return nil, fmt.Errorf("after_job_id and after_received_at must be provided together")
	}

	jobID, err := uuid.Parse(jobIDRaw)
	if err != nil {
		return nil, fmt.Errorf("invalid after_job_id")
	}

	receivedAt, err := time.Parse(time.RFC3339Nano, receivedAtRaw)
	if err != nil {
		return nil, fmt.Errorf("invalid after_received_at")
	}

	return &domain.Cursor{JobID: jobID, ReceivedAt: receivedAt}, nil
}

func parseQueryInt(r *http.Request, key string, defaultValue int) (int, error) {
	raw := r.URL.Query().Get(key)
	if raw == "" {
		return defaultValue, nil
	}

	value, err := strconv.Atoi(raw)
	if err != nil {
		return 0, err
	}

	return value, nil
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	if err := json.NewEncoder(w).Encode(payload); err != nil {
		slog.Error("failed to encode response", "err", err)
	}
}

func writeError(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]string{"error": message})
}
