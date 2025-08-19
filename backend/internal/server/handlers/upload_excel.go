package handlers

import (
	"net/http"
	"strings"
)

const maxFileSize = 10 << 20

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

	if err := h.resProcessor.ProcessAddingExcelFile(r.Context(), header.Filename, file); err != nil {
		MustEncodeErrorMsg(w, err, http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
