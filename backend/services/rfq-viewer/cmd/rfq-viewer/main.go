package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/app"
	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/config"
)

func main() {
	slog.SetDefault(slog.New(slog.NewJSONHandler(os.Stdout, nil)))

	cfg, err := config.Load()
	if err != nil {
		slog.Error("failed to load config", "err", err)
		os.Exit(1)
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	a, err := app.New(ctx, cfg)
	if err != nil {
		slog.Error("failed to start app", "err", err)
		os.Exit(1)
	}
	defer a.Close()

	if err := a.Run(ctx); err != nil {
		slog.Error("app stopped with error", "err", err)
		os.Exit(1)
	}

	slog.Info("app stopped")
}
