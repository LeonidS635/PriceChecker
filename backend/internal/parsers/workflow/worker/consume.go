package worker

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners/pool"
)

func (w ParserWorker) Start(ctx context.Context) error {
	pp, err := pool.NewParserPool(w.spawner)
	if err != nil {
		return err
	}

	go func() {
		for {
			select {
			case <-w.baseCtx.Done():
				return
			case task := <-w.tasksQueue:
				pp.Search(ctx, task)
			}
		}
	}()

	return nil
}
