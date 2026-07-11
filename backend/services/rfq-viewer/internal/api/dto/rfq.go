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

type Cursor struct {
	JobID      string    `json:"job_id"`
	ReceivedAt time.Time `json:"received_at"`
}

type ClientRFQsPage struct {
	Items      []RFQ   `json:"items"`
	NextCursor *Cursor `json:"next_cursor,omitempty"`
}
