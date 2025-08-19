package dto

import "github.com/LeonidS635/PriceChecker/backend/internal/dto/conditions"

type Offer struct {
	PartNumber       string        `json:"part_number"`
	Description      string        `json:"description"`
	Price            float32       `json:"price"`
	QTY              int           `json:"qty"`
	Condition        conditions.ID `json:"condition_id"`
	Warehouse        string        `json:"warehouse"`
	LeadTime         string        `json:"lead_time"`
	Interchangeable  []string      `json:"interchangeable"`
	OtherInformation string        `json:"other_information"`
}
