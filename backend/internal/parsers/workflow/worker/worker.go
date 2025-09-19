package worker

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/types"
)

type pool interface {
	Login(ctx context.Context, username string, password string) error
	Logout(ctx context.Context) error
	Search(task types.Task)
}

type Worker struct {
	tasksQueue chan types.Task
	pool       pool
}

const queueSize = 100

func New(ctx context.Context, p pool) (Worker, error) {
	w := Worker{
		tasksQueue: make(chan types.Task, queueSize),
		pool:       p,
	}

	go w.start(ctx)

	return w, nil
}
