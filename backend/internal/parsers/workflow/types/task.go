package types

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/results"
)

type Task = struct {
	PartNumber string
	ResChan    chan<- results.SearchResult
}
