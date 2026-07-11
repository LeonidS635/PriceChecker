package dto

import (
	"time"

	"github.com/google/uuid"
)

type ExtractionResult struct {
	SchemaVersion   string          `json:"schema_version"`
	JobID           uuid.UUID       `json:"job_id"`
	SourceMessageID string          `json:"source_message_id"`
	ClientID        uint64          `json:"client_id"`
	SenderEmail     string          `json:"sender_email"`
	Subject         string          `json:"subject"`
	ReceivedAt      time.Time       `json:"received_at"`
	ProcessedAt     time.Time       `json:"processed_at"`
	Parts           []ExtractedPart `json:"parts"`
}

type ExtractedPart struct {
	PartNumber   string   `json:"part_number"`
	Description  *string  `json:"description"`
	Quantity     *int     `json:"quantity"`
	Alternatives []string `json:"alternatives"`
}
