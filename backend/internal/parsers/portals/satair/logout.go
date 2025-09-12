package satair

import (
	"context"
)

func (s SatAir) configureLogout() {
	s.logoutC.AllowURLRevisit = true
}

func (s SatAir) Logout(ctx context.Context) error {
	return s.logoutC.Post(logoutURL, nil)
}
