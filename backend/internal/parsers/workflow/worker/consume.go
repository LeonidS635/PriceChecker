package worker

import (
	"context"
)

func (w Worker) start(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case task := <-w.tasksQueue:
			w.pool.Search(task)
		}
	}
}
