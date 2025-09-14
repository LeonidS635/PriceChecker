package pool

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/results"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/types"
)

type ParserPool struct {
	parsers chan parsers.Parser
}

func NewParserPool(spawner spawners.Spawner) (ParserPool, error) {
	rateLimit := spawner.GetRateLimit()
	pp := ParserPool{
		parsers: make(chan parsers.Parser, rateLimit),
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

func (pp ParserPool) Login(ctx context.Context, username string, password string) error {
	if parser := pp.get(ctx); parser != nil {
		defer pp.put(parser)
		return parser.Login(ctx, username, password)
	}
	return nil
}

func (pp ParserPool) Logout(ctx context.Context) error {
	if parser := pp.get(ctx); parser != nil {
		defer pp.put(parser)
		return parser.Logout(ctx)
	}
	return nil
}

func (pp ParserPool) Search(task types.Task) {
	if parser := pp.get(task.Ctx); parser != nil {
		go func() {
			defer pp.put(parser)

			offers, err := parser.Search(task.Ctx, task.PartNumber)
			task.ResChan <- results.SearchResult{Offers: offers, Err: err} // TODO: respect ctx
		}()
	}
}

func (pp ParserPool) get(ctx context.Context) parsers.Parser {
	select {
	case searcher := <-pp.parsers:
		return searcher
	case <-ctx.Done():
		return nil
	}
}

func (pp ParserPool) put(parser parsers.Parser) {
	pp.parsers <- parser
}
