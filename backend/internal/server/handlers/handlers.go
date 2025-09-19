package handlers

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/results/processor"
)

type Handler struct {
	resProcessor processor.ResultsProcessor
}

func NewHandler(ctx context.Context) (Handler, error) {
	p, err := processor.NewResultsProcessor(ctx)
	if err != nil {
		return Handler{}, err
	}
	return Handler{resProcessor: p}, nil
}
