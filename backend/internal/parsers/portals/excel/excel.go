package excel

import (
	"context"
	"errors"
	"strconv"
	"strings"

	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers"
	"github.com/LeonidS635/PriceChecker/backend/internal/parsers/portals/utils"
	"github.com/xuri/excelize/v2"
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

func (e Excel) Logout(ctx context.Context) error {
	return nil
}

func (e Excel) Search(ctx context.Context, partNumber string) ([]dto.Offer, error) {
	f, err := excelize.OpenFile(e.path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	sheets := f.GetSheetList()
	if len(sheets) == 0 {
		return nil, errors.New("empty excel file")
	}

	rows, err := f.GetRows(sheets[0])
	if err != nil {
		return nil, err
	}

	if len(rows) == 0 {
		return nil, errors.New("empty sheet")
	}

	headers := rows[0]
	offers := make([]dto.Offer, 0)

	for _, row := range rows[1:] {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		default:
		}

		product := make(map[string]string)
		for i, header := range headers {
			if i < len(row) {
				product[header] = row[i]
			} else {
				product[header] = ""
			}
		}

		if product["part number"] == partNumber && product["description"] != "No such part" {
			price, _ := utils.GetPriceFromString(product["price"])
			qty, _ := strconv.Atoi(product["qty"])
			offer := dto.Offer{
				PartNumber:       product["part number"],
				Description:      product["description"],
				Price:            price,
				QTY:              qty,
				Condition:        conditions.GetID(product["condition_id"]),
				Warehouse:        product["warehouse"],
				LeadTime:         product["lead time"],
				Interchangeable:  strings.Split(product["interchangeable"], ","),
				OtherInformation: product["other information"],
			}
			offers = append(offers, offer)
		}
	}

	return offers, nil
}
