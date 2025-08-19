package worker

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/types"
)

const queueSize = 100

type ParserWorker struct {
	baseCtx    context.Context
	spawner    spawners.Spawner
	tasksQueue chan types.Task
}

func NewParserWorker(ctx context.Context, spawner spawners.Spawner) ParserWorker {
	return ParserWorker{
		baseCtx:    ctx,
		spawner:    spawner,
		tasksQueue: make(chan types.Task, queueSize),
	}
}
