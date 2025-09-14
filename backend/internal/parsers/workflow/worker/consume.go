package worker

import (
	"context"
)

func (w ParserWorker) start(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case task := <-w.tasksQueue:
			w.pp.Search(task)
		}
	}
}
