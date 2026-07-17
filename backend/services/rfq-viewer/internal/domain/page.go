package domain

import (
	"time"

	"github.com/google/uuid"
)

type Cursor struct {
	ReceivedAt time.Time
	JobID      uuid.UUID
	PartID     uint64
}

type RFQPage struct {
	Items      []RFQ
	NextCursor *Cursor
}
