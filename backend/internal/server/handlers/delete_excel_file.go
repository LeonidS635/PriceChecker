package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
)

type (
	deleteExcelFileRequest  = struct{
		FileID domain.PortalID `json:"file_id"`
	}
	deleteExcelFileResponse = struct {
		Success bool   `json:"success"`
		Error   string `json:"error"`
	}
)

func (h Handler) DeleteExcelFile(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	var req deleteExcelFileRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		MustEncodeErrorMsg(w, err, http.StatusBadRequest)
		return
	}

	var resp deleteExcelFileResponse
	// if err := h.resProcessor.ProcessUploadingExcelFile(r.Context(), header.Filename, file); err != nil {
	// 	resp.Success = false
	// 	resp.Error = err.Error()
	// } else {
	// 	resp.Success = true
	// }

	w.WriteHeader(http.StatusCreated)
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		MustEncodeErrorMsg(w, err, http.StatusInternalServerError)
	}
}
