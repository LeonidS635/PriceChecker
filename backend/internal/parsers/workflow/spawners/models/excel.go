package models

import (
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
)

type ExcelSpawner struct {
	path              string
	portalConstructor func(path string) parsers.Parser
}

func NewExcelSpawner(portalConstructor func(path string) parsers.Parser, path string) Spawner {
	return &ExcelSpawner{
		path:              path,
		portalConstructor: portalConstructor,
	}
}

func (e *ExcelSpawner) Base() parsers.Authenticator {
	return e.portalConstructor(e.path)
}

func (e *ExcelSpawner) Spawn() (parsers.Parser, error) {
	return e.portalConstructor(e.path), nil
}

func (e *ExcelSpawner) GetRateLimit() int {
	return -1 // Will be replaced later
}
