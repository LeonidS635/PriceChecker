package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/LeonidS635/PriceChecker/backend/internal/server/handlers/quotation"
)

type (
	makeQuotationRequest  = quotation.Request
	makeQuotationResponse = struct{}
)

func (h Handler) FormQuotation(w http.ResponseWriter, r *http.Request) {
	var req makeQuotationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		MustEncodeErrorMsg(w, err, http.StatusBadRequest)
		return
	}

	q := quotation.Form(req)

	filename := fmt.Sprintf("quotation_SQ%d.xlsx", req.QuotationN)
	w.Header().Set("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s\"", filename))

	if err := q.Write(w); err != nil {
		http.Error(w, "Error generating Excel file", http.StatusInternalServerError)
		return
	}
}
