package types

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/results"
)

type Promise struct {
	ResultChan <-chan results.SearchResult
	Err        error
}
