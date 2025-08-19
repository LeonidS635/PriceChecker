package handlers

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/results/processor"
)

type Handler struct {
	resProcessor processor.ResultsProcessor
}

func NewHandler(ctx context.Context) Handler {
	return Handler{resProcessor: processor.NewResultsProcessor(ctx)}
}
