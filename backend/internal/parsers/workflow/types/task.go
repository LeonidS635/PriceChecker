package types

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/results"
)

type Task = struct {
	Ctx        context.Context
	PartNumber string
	ResChan    chan<- results.SearchResult
}
