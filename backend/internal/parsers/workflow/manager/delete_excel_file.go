package manager

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
)

func deleteExcelFileFromDisk(name string, content io.Reader) error {
	filePath := filepath.Join(excelDirPath, name)
	if err := os.Remove(filePath); err != nil {
		return fmt.Errorf("failed to delete from disk: %w", err)
	}
	return nil
}

func (m Manager) DeleteExcelFile(ctx context.Context, name string, content io.Reader) (err error) {
	defer func ()  {
		if err != nil {
			err = fmt.Errorf("failed to delete %s: %w", name, err)
		}
	}()

	err = deleteExcelFileFromDisk(name, content)
	if err != nil {
		return
	}

	// TODO: remove file from spawners and workers
	
	return
}
