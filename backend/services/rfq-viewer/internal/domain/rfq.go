package domain

import (
	"time"

	"github.com/google/uuid"
)

type RFQ struct {
	JobID           uuid.UUID
	ClientID        uint64
	SenderEmail     string
	SourceMessageID string
	Subject         string
	ReceivedAt      time.Time
	ProcessedAt     time.Time
	Parts           []Part
}

type Part struct {
	ID           uint64
	PartNumber   string
	Description  *string
	Quantity     *int
	Alternatives []string
}
