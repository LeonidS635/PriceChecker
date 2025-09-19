package server

import (
	"context"
	"log"
	"net"
	"net/http"

	"github.com/LeonidS635/PriceChecker/backend/internal/server/handlers"
)

func corsHandler(next http.Handler) http.Handler {
	return http.HandlerFunc(
		func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusNoContent)
				return
			}

			next.ServeHTTP(w, r)
		},
	)
}

func StartUpServer(ctx context.Context, addr string) error {
	handler, err := handlers.NewHandler(ctx)
	if err != nil {
		return err
	}

	router := http.NewServeMux()
	router.HandleFunc("GET /config", handler.GetConfig)
	router.HandleFunc("POST /login", handler.Login)
	router.HandleFunc("POST /logout", handler.Logout)
	router.HandleFunc("POST /search", handler.Search)
	router.HandleFunc("POST /excel", handler.UploadExcelFile)
	router.HandleFunc("DELETE /excel", handler.DeleteExcelFile)
	router.HandleFunc("POST /quotation", handler.FormQuotation)

	server := http.Server{
		Addr:        addr,
		BaseContext: func(net.Listener) context.Context { return ctx },
		Handler:     corsHandler(router),
	}

	log.Println("Starting server on", server.Addr)
	return server.ListenAndServe()
}
