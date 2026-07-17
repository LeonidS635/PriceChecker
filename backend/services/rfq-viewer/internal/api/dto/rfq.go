package dto

import "time"

type Part struct {
	PartNumber   string   `json:"part_number"`
	Description  *string  `json:"description,omitempty"`
	Quantity     *int     `json:"quantity,omitempty"`
	Alternatives []string `json:"alternatives,omitempty"`
}

type RFQ struct {
	ClientName string    `json:"client_name"`
	Subject    string    `json:"subject"`
	ReceivedAt time.Time `json:"received_at"`
	Parts      []Part    `json:"parts"`
}

type ClientRFQsPage struct {
	Items      []RFQ      `json:"items"`
	Pagination Pagination `json:"pagination,omitempty"`
}

type Pagination struct {
	HasNext bool   `json:"has_next"`
	Next    string `json:"next,omitempty"`
}

type Cursor struct {
	ReceivedAt time.Time `json:"received_at"`
	JobID      string    `json:"job_id"`
	PartID     uint64    `json:"part_id"`
}
