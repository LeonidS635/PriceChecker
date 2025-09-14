package quotation

import (
	"fmt"
	"math"
	"path/filepath"
	"strings"
	"time"

	"github.com/xuri/excelize/v2"
)

type Request struct {
	QuotationN int `json:"quotation_number"`
	Offers     []struct {
		PartNumber  string  `json:"part_number"`
		Description string  `json:"description"`
		Condition   string  `json:"condition"`
		QTY         int     `json:"qty"`
		Price       float32 `json:"price"`
		LeadTime    int     `json:"lead_time"`
	} `json:"offers"`
	PaymentTerms  string  `json:"payment_terms"`
	Incoterms     string  `json:"incoterms"`
	LogisticsCost float32 `json:"logistics_cost"`
	Markup        float32 `json:"markup"`
}

func Form(req Request) *excelize.File {
	// Создаем новый Excel файл
	f := excelize.NewFile()
	defer func() {
		if err := f.Close(); err != nil {
			fmt.Printf("Error closing Excel file: %v\n", err)
		}
	}()

	// Получаем активный лист
	sheetName := f.GetSheetName(0)

	// Установка ширины колонок
	f.SetColWidth(sheetName, "A", "A", 14)
	f.SetColWidth(sheetName, "B", "B", 14)
	f.SetColWidth(sheetName, "C", "C", 13)
	f.SetColWidth(sheetName, "D", "D", 5.5)
	f.SetColWidth(sheetName, "E", "E", 11.5)
	f.SetColWidth(sheetName, "F", "F", 12.5)
	f.SetColWidth(sheetName, "G", "G", 12)

	headerBackgroundStyle, _ := f.NewStyle(
		&excelize.Style{
			Fill: excelize.Fill{
				Type:    "pattern",
				Pattern: 1,
				Color:   []string{"#D9D9D9"},
			},
			Border: []excelize.Border{
				{Type: "left", Color: "#FFFFFF", Style: 0},
				{Type: "right", Color: "#FFFFFF", Style: 0},
				{Type: "top", Color: "#FFFFFF", Style: 0},
				{Type: "bottom", Color: "#FFFFFF", Style: 0},
			},
		},
	)
	f.SetCellStyle(sheetName, "A1", "G6", headerBackgroundStyle)

	imgPath, _ := filepath.Abs("internal/server/handlers/quotation/assets/header_left.png")
	f.MergeCell(sheetName, "A1", "C6")
	f.AddPicture(
		sheetName, "A1", imgPath, &excelize.GraphicOptions{
			AutoFit:         true,
			LockAspectRatio: true,
			OffsetX:         5,
			OffsetY:         5,
		},
	)

	imgPath, _ = filepath.Abs("internal/server/handlers/quotation/assets/header_right.png")
	f.MergeCell(sheetName, "D1", "G6")
	f.AddPicture(
		sheetName, "E1", imgPath, &excelize.GraphicOptions{
			ScaleY:          0.85,
			AutoFit:         true,
			LockAspectRatio: true,
			OffsetX:         5,
			OffsetY:         5,
		},
	)

	mainContentBackgroundStyle, _ := f.NewStyle(
		&excelize.Style{
			Fill: excelize.Fill{
				Type:    "pattern",
				Pattern: 1,
				Color:   []string{"#FFFFFF"},
			},
			Border: []excelize.Border{
				{Type: "left", Color: "#FFFFFF", Style: 0},
				{Type: "right", Color: "#FFFFFF", Style: 0},
				{Type: "top", Color: "#FFFFFF", Style: 0},
				{Type: "bottom", Color: "#FFFFFF", Style: 0},
			},
		},
	)
	f.SetCellStyle(sheetName, "A7", fmt.Sprintf("G%d", 17+len(req.Offers)+5), mainContentBackgroundStyle)

	// Номер квотации
	quotationStyle, _ := f.NewStyle(
		&excelize.Style{
			Fill: excelize.Fill{
				Type:    "pattern",
				Pattern: 1,
				Color:   []string{"#FFFFFF"},
			},
			Font: &excelize.Font{
				Bold:   true,
				Italic: true,
				Size:   16,
			},
			Border: []excelize.Border{
				{Type: "left", Color: "#FFFFFF", Style: 0},
				{Type: "right", Color: "#FFFFFF", Style: 0},
				{Type: "top", Color: "#FFFFFF", Style: 0},
				{Type: "bottom", Color: "#FFFFFF", Style: 0},
			},
		},
	)
	f.SetCellStyle(sheetName, "A8", "A8", quotationStyle)
	f.SetCellValue(sheetName, "A8", "Quotation")

	quotationNumberStyle, _ := f.NewStyle(
		&excelize.Style{
			Fill: excelize.Fill{
				Type:    "pattern",
				Pattern: 1,
				Color:   []string{"#FFFFFF"},
			},
			Font: &excelize.Font{
				Bold: true,
				Size: 16,
			},
			Border: []excelize.Border{
				{Type: "left", Color: "#FFFFFF", Style: 0},
				{Type: "right", Color: "#FFFFFF", Style: 0},
				{Type: "top", Color: "#FFFFFF", Style: 0},
				{Type: "bottom", Color: "#FFFFFF", Style: 0},
			},
		},
	)
	f.SetCellStyle(sheetName, "B8", "B8", quotationNumberStyle)
	f.SetCellValue(sheetName, "B8", fmt.Sprintf("SQ%d", req.QuotationN))

	// Дополнительная информация
	textStyle, _ := f.NewStyle(
		&excelize.Style{
			Fill: excelize.Fill{
				Type:    "pattern",
				Pattern: 1,
				Color:   []string{"#FFFFFF"},
			},
			Font: &excelize.Font{
				Family: "Calibri",
				Size:   11,
			},
			Border: []excelize.Border{
				{Type: "left", Color: "#FFFFFF", Style: 0},
				{Type: "right", Color: "#FFFFFF", Style: 0},
				{Type: "top", Color: "#FFFFFF", Style: 0},
				{Type: "bottom", Color: "#FFFFFF", Style: 0},
			},
			Alignment: &excelize.Alignment{
				Horizontal: "right",
				Vertical:   "center",
			},
		},
	)
	f.SetCellStyle(sheetName, "G8", "G9", textStyle)
	f.SetCellValue(sheetName, "G8", "Found a better price?")
	f.SetCellValue(sheetName, "G9", "We will match any like for like quote!")

	// Информация о квотации
	infoHeadersStyle, _ := f.NewStyle(
		&excelize.Style{
			Fill: excelize.Fill{
				Type:    "pattern",
				Pattern: 1,
				Color:   []string{"#FFFFFF"},
			},
			Font: &excelize.Font{
				Bold:   true,
				Family: "Calibri",
				Size:   11,
			},
			Border: []excelize.Border{
				{Type: "left", Color: "#FFFFFF", Style: 0},
				{Type: "right", Color: "#FFFFFF", Style: 0},
				{Type: "top", Color: "#FFFFFF", Style: 0},
				{Type: "bottom", Color: "#FFFFFF", Style: 0},
			},
			Alignment: &excelize.Alignment{
				Horizontal: "center",
				Vertical:   "center",
			},
		},
	)
	f.SetCellStyle(sheetName, "A12", "A14", infoHeadersStyle)
	f.SetCellValue(sheetName, "A12", "TO")
	f.SetCellValue(sheetName, "A13", "Phone")
	f.SetCellValue(sheetName, "A14", "Email")

	f.SetCellStyle(sheetName, "C12", "C14", infoHeadersStyle)
	f.SetCellValue(sheetName, "C12", "REF#")
	f.SetCellValue(sheetName, "C13", "Payment terms")
	f.SetCellValue(sheetName, "C14", "INCOTERMS")

	f.SetCellStyle(sheetName, "F12", "F14", infoHeadersStyle)
	f.SetCellValue(sheetName, "F12", "Date")
	f.SetCellValue(sheetName, "F13", "Page")
	f.SetCellValue(sheetName, "F14", "Prepared By")

	infoValuesStyle, _ := f.NewStyle(
		&excelize.Style{
			Fill: excelize.Fill{
				Type:    "pattern",
				Pattern: 1,
				Color:   []string{"#FFFFFF"},
			},
			Font: &excelize.Font{
				Family: "Calibri",
				Size:   9,
			},
			Border: []excelize.Border{
				{Type: "left", Color: "#FFFFFF", Style: 0},
				{Type: "right", Color: "#FFFFFF", Style: 0},
				{Type: "top", Color: "#FFFFFF", Style: 0},
				{Type: "bottom", Color: "#FFFFFF", Style: 0},
			},
			Alignment: &excelize.Alignment{
				Horizontal: "center",
				Vertical:   "center",
			},
		},
	)
	f.SetCellStyle(sheetName, "D12", "E14", infoValuesStyle)
	f.MergeCell(sheetName, "D12", "E12")
	f.MergeCell(sheetName, "D13", "E13")
	f.MergeCell(sheetName, "D14", "E14")
	f.SetCellValue(sheetName, "D13", strings.ToUpper(req.PaymentTerms))
	f.SetCellValue(sheetName, "D14", strings.ToUpper(req.Incoterms))

	f.SetCellStyle(sheetName, "G12", "G14", infoValuesStyle)
	f.SetCellValue(sheetName, "G12", time.Now().Format("02.01.2006"))
	f.SetCellValue(sheetName, "G13", "1 of 1")

	// Заголовки таблицы
	tableHeaderStyle, _ := f.NewStyle(
		&excelize.Style{
			Fill: excelize.Fill{
				Type:    "pattern",
				Pattern: 1,
				Color:   []string{"#FFFFFF"},
			},
			Font: &excelize.Font{
				Bold:   true,
				Family: "Calibri",
				Size:   11,
			},
			Border: []excelize.Border{
				{Type: "left", Color: "000000", Style: 1},
				{Type: "right", Color: "000000", Style: 1},
				{Type: "top", Color: "000000", Style: 1},
				{Type: "bottom", Color: "000000", Style: 1},
			},
			Alignment: &excelize.Alignment{
				Horizontal: "center",
				Vertical:   "center",
			},
		},
	)
	f.SetCellStyle(sheetName, "A16", "G16", tableHeaderStyle)
	f.SetCellValue(sheetName, "A16", "Part Number")
	f.SetCellValue(sheetName, "B16", "Description")
	f.SetCellValue(sheetName, "C16", "QTY")
	f.SetCellValue(sheetName, "D16", "CD")
	f.SetCellValue(sheetName, "E16", "Price,ea")
	f.SetCellValue(sheetName, "F16", "Total")
	f.SetCellValue(sheetName, "G16", "LT to MOW")

	// Заполнение данных из offers
	tableBodyStyle, _ := f.NewStyle(
		&excelize.Style{
			Fill: excelize.Fill{
				Type:    "pattern",
				Pattern: 1,
				Color:   []string{"#FFFFFF"},
			},
			Border: []excelize.Border{
				{Type: "left", Color: "000000", Style: 1},
				{Type: "right", Color: "000000", Style: 1},
				{Type: "top", Color: "000000", Style: 1},
				{Type: "bottom", Color: "000000", Style: 1},
			},
			Font: &excelize.Font{
				Family: "Calibri",
				Size:   10,
			},
			Alignment: &excelize.Alignment{
				Horizontal: "center",
				Vertical:   "center",
				WrapText:   true,
			},
		},
	)
	tableBodyPriceStyle, _ := f.NewStyle(
		&excelize.Style{
			Fill: excelize.Fill{
				Type:    "pattern",
				Pattern: 1,
				Color:   []string{"#FFFFFF"},
			},
			Border: []excelize.Border{
				{Type: "left", Color: "000000", Style: 1},
				{Type: "right", Color: "000000", Style: 1},
				{Type: "top", Color: "000000", Style: 1},
				{Type: "bottom", Color: "000000", Style: 1},
			},
			Font: &excelize.Font{
				Family: "Calibri",
				Size:   10,
			},
			Alignment: &excelize.Alignment{
				Horizontal: "center",
				Vertical:   "center",
			},
			NumFmt: 165,
		},
	)
	f.SetCellStyle(sheetName, "A17", fmt.Sprintf("G%d", 16+len(req.Offers)), tableBodyStyle)

	var itemsTotal float32
	currentRow := 17

	for _, offer := range req.Offers {
		// Расчет финальной цены: ОКРУГЛ(базовая цена * наценка + логистика / количество)
		finalPrice := math.Round(float64(offer.Price*(1+req.Markup/100) + req.LogisticsCost/float32(offer.QTY)))
		if offer.Price == 0 {
			finalPrice = 0
		}
		totalPrice := float32(finalPrice) * float32(offer.QTY)
		itemsTotal += totalPrice

		f.SetCellValue(sheetName, fmt.Sprintf("A%d", currentRow), offer.PartNumber)
		f.SetCellValue(sheetName, fmt.Sprintf("B%d", currentRow), offer.Description)
		f.SetCellValue(sheetName, fmt.Sprintf("C%d", currentRow), offer.QTY)
		f.SetCellValue(sheetName, fmt.Sprintf("D%d", currentRow), offer.Condition)

		f.SetCellStyle(sheetName, fmt.Sprintf("E%d", currentRow), fmt.Sprintf("F%d", currentRow), tableBodyPriceStyle)
		f.SetCellValue(sheetName, fmt.Sprintf("E%d", currentRow), finalPrice)
		f.SetCellValue(sheetName, fmt.Sprintf("F%d", currentRow), totalPrice)

		var leadTime string
		if offer.LeadTime == 1 {
			leadTime = "1 day"
		} else if offer.LeadTime > 1 {
			leadTime = fmt.Sprintf("%d days", offer.LeadTime)
		}
		f.SetCellValue(sheetName, fmt.Sprintf("G%d", currentRow), leadTime)

		currentRow++
	}

	// Итоговые строки (начинаем с строки после последнего товара + 1)
	totalStartRow := currentRow + 1

	totalStyle, _ := f.NewStyle(
		&excelize.Style{
			Fill: excelize.Fill{
				Type:    "pattern",
				Pattern: 1,
				Color:   []string{"#FFFFFF"},
			},
			Font: &excelize.Font{
				Family: "Calibri",
				Size:   11,
			},
			Border: []excelize.Border{
				{Type: "left", Color: "#FFFFFF", Style: 0},
				{Type: "right", Color: "#FFFFFF", Style: 0},
				{Type: "top", Color: "#FFFFFF", Style: 0},
				{Type: "bottom", Color: "#FFFFFF", Style: 0},
			},
			Alignment: &excelize.Alignment{
				Horizontal: "right",
				Vertical:   "bottom",
			},
		},
	)
	totalPriceStyle, _ := f.NewStyle(
		&excelize.Style{
			Fill: excelize.Fill{
				Type:    "pattern",
				Pattern: 1,
				Color:   []string{"#FFFFFF"},
			},
			Font: &excelize.Font{
				Family: "Calibri",
				Size:   11,
			},
			Border: []excelize.Border{
				{Type: "left", Color: "#FFFFFF", Style: 0},
				{Type: "right", Color: "#FFFFFF", Style: 0},
				{Type: "top", Color: "#FFFFFF", Style: 0},
				{Type: "bottom", Color: "#FFFFFF", Style: 0},
			},
			Alignment: &excelize.Alignment{
				Horizontal: "right",
				Vertical:   "bottom",
			},
			NumFmt: 165,
		},
	)
	f.SetCellStyle(sheetName, fmt.Sprintf("F%d", totalStartRow), fmt.Sprintf("F%d", totalStartRow+3), totalStyle)
	f.SetCellStyle(sheetName, fmt.Sprintf("G%d", totalStartRow), fmt.Sprintf("G%d", totalStartRow+3), totalPriceStyle)

	f.SetCellValue(sheetName, fmt.Sprintf("F%d", totalStartRow), "Items Total")
	f.SetCellValue(sheetName, fmt.Sprintf("G%d", totalStartRow), itemsTotal)

	f.SetCellValue(sheetName, fmt.Sprintf("F%d", totalStartRow+1), "Freight")
	f.SetCellValue(sheetName, fmt.Sprintf("G%d", totalStartRow+1), 0)

	f.SetCellValue(sheetName, fmt.Sprintf("F%d", totalStartRow+2), "VAT")
	f.SetCellValue(sheetName, fmt.Sprintf("G%d", totalStartRow+2), 0)

	f.SetCellValue(sheetName, fmt.Sprintf("F%d", totalStartRow+3), "Total If Paying By Bank Transfer")
	f.SetCellValue(sheetName, fmt.Sprintf("G%d", totalStartRow+3), itemsTotal)

	newSheet, _ := f.NewSheet("Sheet2")
	newSheetName := f.GetSheetName(newSheet)

	redTextStyle, _ := f.NewStyle(
		&excelize.Style{
			Font: &excelize.Font{
				Family: "Calibri",
				Size:   11,
				Color:  "#FF0000",
			},
		},
	)
	f.SetCellStyle(newSheetName, "A1", "A1", redTextStyle)
	f.SetCellValue(newSheetName, "A1", "Ship via: Freight Forwarder ( FREIGHT CHARGES WILL BE INVOICED SEPARATELY )")

	plainTextStyle, _ := f.NewStyle(
		&excelize.Style{
			Font: &excelize.Font{
				Family: "Calibri",
				Size:   11,
			},
		},
	)
	f.SetCellStyle(newSheetName, "A2", "A2", plainTextStyle)
	f.SetCellValue(newSheetName, "A2", "NOT CACHEABLE // NOT RETURNABLE")

	return f
}
