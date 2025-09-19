package manager

import (
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/pool"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/worker"
)

const excelDirPath = "./uploads"

func init() {
	if err := os.MkdirAll(excelDirPath, os.ModePerm); err != nil {
		panic(err)
	}
}

func saveExcelFileOnDisk(name string, content io.Reader) error {
	filePath := filepath.Join(excelDirPath, name)
	file, err := os.OpenFile(filePath, os.O_CREATE|os.O_WRONLY, 0444)
	if err != nil && !errors.Is(err, os.ErrExist) {
		return fmt.Errorf("failed to save: %w", err)
	}
	defer file.Close()

	_, err = io.Copy(file, content)
	if err != nil {
		return fmt.Errorf("failed to save: %w", err)
	}
	return err
}

func (m Manager) UploadExcelFile(ctx context.Context, name string, content io.Reader) (err error) {
	defer func ()  {
		if err != nil {
			err = fmt.Errorf("failed to upload %s: %w", name, err)
		}
	}()

	err = saveExcelFileOnDisk(name, content)
	if err != nil {
		return
	}

	fileID, spawner := spawners.RegisterExcelSpawner(filepath.Join(excelDirPath, name))

	p, err := pool.New(spawner)
	if err != nil {
		return
	}

	w, err := worker.New(m.baseCtx, p)
	if err != nil {
		return
	}
	m.workers[fileID] = w
	
	return
}
