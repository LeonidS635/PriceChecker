package handlers

import (
	"encoding/json"
	"log"
	"net/http"
)

func MustEncodeErrorMsg(w http.ResponseWriter, err error, code int) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(code)
	if marshalError := json.NewEncoder(w).Encode(
		struct {
			Error string `json:"error"`
		}{err.Error()},
	); marshalError != nil {
		w.WriteHeader(http.StatusInternalServerError)
	}
	log.Println(err.Error())
}
