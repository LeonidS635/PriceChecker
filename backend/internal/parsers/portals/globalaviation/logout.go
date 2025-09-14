package globalaviation

import "context"

func (g GlobalAviation) configureLogout() {
	g.logoutC.AllowURLRevisit = true
}

func (g GlobalAviation) Logout(ctx context.Context) error {
	return nil
}