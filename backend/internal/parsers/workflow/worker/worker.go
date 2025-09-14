package worker

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners/pool"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/types"
)

const queueSize = 100

type ParserWorker struct {
	spawner    spawners.Spawner
	tasksQueue chan types.Task

	pp pool.ParserPool
}

func NewParserWorker(ctx context.Context, spawner spawners.Spawner) ParserWorker {
	pp, _ := pool.NewParserPool(spawner)
	w := ParserWorker{
		spawner:    spawner,
		tasksQueue: make(chan types.Task, queueSize),
		pp:         pp,
	}

	go w.start(ctx)

	return w
}
