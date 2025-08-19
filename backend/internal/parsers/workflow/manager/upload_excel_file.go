package manager

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/workflow/spawners"
)

const excelDirPath = "./uploads"

func init() {
	if err := os.MkdirAll(excelDirPath, os.ModePerm); err != nil {
		panic(err)
	}
}

func saveExcelFileOnDisk(name string, content io.Reader) error {
	filePath := filepath.Join(excelDirPath, name)
	file, err := os.OpenFile(filePath, os.O_CREATE|os.O_EXCL|os.O_WRONLY, os.ModePerm)
	if err != nil && !errors.Is(err, os.ErrExist) {
		return fmt.Errorf("failed to save file %s: %w", name, err)
	}
	defer file.Close()

	_, err = io.Copy(file, content)
	return err
}

func (m Manager) AddExcelFile(ctx context.Context, name string, content io.Reader) error {
	log.Println("saving", name)
	if err := saveExcelFileOnDisk(name, content); err != nil {
		return err
	}

	fileID := spawners.RegisterExcelSpawner(filepath.Join(excelDirPath, name))

	return m.Login(ctx, []domain.PortalID{fileID})[fileID]
}
