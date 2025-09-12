package worker

import (
	"context"
)

func (w ParserWorker) start(ctx context.Context) {
	//pp, err := pool.NewParserPool(w.spawner)
	//if err != nil {
	//	return err
	//}

	for {
		select {
		case <-w.baseCtx.Done():
			return
		case task := <-w.tasksQueue:
			w.pp.Search(ctx, task)
		}
	}
}
