package app

import (
	"context"
	"fmt"
	"log/slog"
	"net"
	"net/http"
	"time"

	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/api"
	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/config"
	natsconsumer "github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/consumer"
	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/service"
	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/storage/db"
	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/storage/facade"
	txmanager "github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/storage/tx-manager"
	"github.com/jackc/pgx/v5/pgxpool"
)

type App struct {
	pool     *pgxpool.Pool
	consumer *natsconsumer.Consumer
	httpAddr string
	handler  *api.Handler
}

func New(ctx context.Context, cfg config.Config) (*App, error) {
	pool, err := pgxpool.New(ctx, cfg.PGDSN())
	if err != nil {
		return nil, fmt.Errorf("connect to database: %w", err)
	}

	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("ping database: %w", err)
	}

	storage := db.NewDB(pool)
	storageFacade := facade.NewStorageFacade(storage, txmanager.NewTxManager(pool))
	rfqService := service.NewRFQService(storageFacade)

	natsConsumer, err := natsconsumer.New(natsconsumer.Config{
		URL:        cfg.NATSURL,
		Stream:     cfg.NATSStream,
		Subject:    cfg.NATSSubject,
		Durable:    cfg.NATSDurable,
		MaxDeliver: cfg.NATSMaxDeliver,
	}, rfqService)
	if err != nil {
		pool.Close()
		return nil, fmt.Errorf("create nats consumer: %w", err)
	}

	return &App{
		pool:     pool,
		consumer: natsConsumer,
		httpAddr: cfg.HTTPAddr,
		handler:  api.NewHandler(rfqService),
	}, nil
}

func (a *App) Run(ctx context.Context) error {
	errCh := make(chan error, 2)

	go func() {
		errCh <- a.runConsumer(ctx)
	}()

	go func() {
		errCh <- a.runHTTP(ctx)
	}()

	select {
	case <-ctx.Done():
		return nil
	case err := <-errCh:
		return err
	}
}

func (a *App) runConsumer(ctx context.Context) error {
	return a.consumer.Run(ctx)
}

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

func (a *App) runHTTP(ctx context.Context) error {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /clients/{clientID}/rfqs", a.handler.GetClientRFQs)

	httpServer := &http.Server{
		Addr:    a.httpAddr,
		Handler: corsHandler(mux),
		BaseContext: func(net.Listener) context.Context {
			return ctx
		},
	}

	go func() {
		<-ctx.Done()

		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()

		if err := httpServer.Shutdown(shutdownCtx); err != nil {
			slog.Error("failed to shutdown http server", "err", err)
		}
	}()

	slog.Info("HTTP server started", "addr", a.httpAddr)

	err := httpServer.ListenAndServe()
	if err == http.ErrServerClosed {
		return nil
	}

	return err
}

func (a *App) Close() {
	if a.consumer != nil {
		a.consumer.Close()
	}
	if a.pool != nil {
		a.pool.Close()
	}
}
