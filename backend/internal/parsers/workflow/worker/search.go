package worker

import (
	"context"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/results"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/types"
)

func (w ParserWorker) Search(ctx context.Context, partNumber string) <-chan results.SearchResult {
	resChan := make(chan results.SearchResult, 1)

	select {
	case <-ctx.Done():
	case w.tasksQueue <- types.Task{PartNumber: partNumber, ResChan: resChan}:
	}

	return resChan
}
