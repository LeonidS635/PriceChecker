package spawners

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
)

type ExcelSpawner struct {
	path              string
	portalConstructor func(path string) parsers.Parser

	spawnedN int
	limit	int
}

func NewExcelSpawner(portalConstructor func(path string) parsers.Parser, path string, limit int) spawner {
	return &ExcelSpawner{
		path:              path,
		portalConstructor: portalConstructor,
		limit: limit,
	}
}

func (e *ExcelSpawner) Spawn() (parsers.Parser, error) {
	if e.spawnedN > e.limit {
		return nil, ErrLimitExceeded
	}

	e.spawnedN++
	return e.portalConstructor(e.path), nil
}

func (e *ExcelSpawner) Limit() int {
	return e.limit
}
