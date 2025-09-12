package worker

import "context"

func (w ParserWorker) Login(ctx context.Context, username string, password string) error {
	// base := w.spawner.Base()
	// return base.Login(ctx, username, password)
	return w.pp.Login(ctx, username, password)
}
