package worker

import "context"

func (w Worker) Logout(ctx context.Context) error {
	return w.pool.Logout(ctx)
}
