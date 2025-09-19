package pool

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/results"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/types"
)

type spawner interface {
	Spawn() (parsers.Parser, error)
	Limit() int
}

type ParsersPool struct {
	parsers chan parsers.Parser
}

func New(s spawner) (ParsersPool, error) {
	limit := s.Limit()
	parsers := make(chan parsers.Parser, limit)

	for range limit {
		searcher, err := s.Spawn()
		if err != nil {
			return ParsersPool{}, err
		}
		parsers <- searcher
	}

	return ParsersPool{parsers: parsers}, nil
}

func (pp ParsersPool) Login(ctx context.Context, username string, password string) error {
	if parser := pp.get(ctx); parser != nil {
		defer pp.put(parser)
		return parser.Login(ctx, username, password)
	}
	return nil
}

func (pp ParsersPool) Logout(ctx context.Context) error {
	if parser := pp.get(ctx); parser != nil {
		defer pp.put(parser)
		return parser.Logout(ctx)
	}
	return nil
}

func (pp ParsersPool) Search(task types.Task) {
	if parser := pp.get(task.Ctx); parser != nil {
		go func() {
			defer pp.put(parser)

			offers, err := parser.Search(task.Ctx, task.PartNumber)
			task.ResChan <- results.SearchResult{Offers: offers, Err: err} // TODO: respect ctx
		}()
	}
}

func (pp ParsersPool) get(ctx context.Context) parsers.Parser {
	select {
	case searcher := <-pp.parsers:
		return searcher
	case <-ctx.Done():
		return nil
	}
}

func (pp ParsersPool) put(parser parsers.Parser) {
	pp.parsers <- parser
}
