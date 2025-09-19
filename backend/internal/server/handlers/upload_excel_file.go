package handlers

import (
	"encoding/json"
	"net/http"
	"strings"
)

const maxFileSize = 1 << 23

type (
	uploadExcelFileRequest  = struct{}
	uploadExcelFileResponse = struct {
		Success bool   `json:"success"`
		Error   string `json:"error"`
	}
)

func (h Handler) UploadExcelFile(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	r.Body = http.MaxBytesReader(w, r.Body, maxFileSize)
	if err := r.ParseMultipartForm(maxFileSize); err != nil {
		MustEncodeErrorMsg(w, err, http.StatusBadRequest)
		return
	}

	file, header, err := r.FormFile("file")
	if err != nil {
		MustEncodeErrorMsg(w, err, http.StatusBadRequest)
		return
	}
	defer file.Close()

	if !strings.HasSuffix(header.Filename, ".xlsx") {
		MustEncodeErrorMsg(w, err, http.StatusBadRequest)
		return
	}

	var resp uploadExcelFileResponse
	if err := h.resProcessor.ProcessUploadingExcelFile(r.Context(), header.Filename, file); err != nil {
		resp.Success = false
		resp.Error = err.Error()
	} else {
		resp.Success = true
	}

	w.WriteHeader(http.StatusCreated)
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		MustEncodeErrorMsg(w, err, http.StatusInternalServerError)
	}
}
