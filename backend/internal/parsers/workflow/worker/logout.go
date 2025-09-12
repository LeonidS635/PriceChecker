package worker

import "context"

func (w ParserWorker) Logout(ctx context.Context) error {
	// base := w.spawner.Base()
	// return base.Logout(ctx)
	return w.pp.Logout(ctx)
}
