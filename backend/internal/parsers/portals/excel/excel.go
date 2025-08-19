package excel

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
)

type Excel struct {
	path string
}

func NewExcelParser(path string) parsers.Parser {
	return Excel{path: path}
}

func (e Excel) Login(ctx context.Context, username string, password string) error {
	return nil
}

func (e Excel) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	return nil, nil
}
