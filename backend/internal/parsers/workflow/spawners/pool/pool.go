package pool

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/results"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/types"
)

type ParserPool struct {
	parsers chan parsers.Searcher
}

func NewParserPool(spawner spawners.Spawner) (ParserPool, error) {
	rateLimit := spawner.GetRateLimit()
	pp := ParserPool{
		parsers: make(chan parsers.Searcher, rateLimit),
	}
	for i := 0; i < rateLimit; i++ {
		searcher, err := spawner.Spawn()
		if err != nil {
			return ParserPool{}, err
		}
		pp.parsers <- searcher
	}

	return pp, nil
}

func (pp ParserPool) Search(ctx context.Context, task types.Task) {
	parser := <-pp.parsers // TODO: respect ctx
	go func() {
		defer func() {
			pp.parsers <- parser
		}()

		offers, err := parser.Search(ctx, task.PartNumber)
		task.ResChan <- results.SearchResult{Offers: offers, Err: err} // TODO: respect ctx
	}()
}
