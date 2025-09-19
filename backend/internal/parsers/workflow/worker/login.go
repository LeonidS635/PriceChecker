package worker

import "context"

func (w Worker) Login(ctx context.Context, username string, password string) error {
	return w.pool.Login(ctx, username, password)
}
