package parsers

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
)

type Authenticator interface {
	Login(ctx context.Context, username string, password string) error
}

type Searcher interface {
	Search(ctx context.Context, partNumber string) ([]dto.Offer, error)
}

type Parser interface {
	Authenticator
	Searcher
}
