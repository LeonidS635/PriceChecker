package domain

import (
	"time"

	"github.com/google/uuid"
)

type Cursor struct {
	JobID      uuid.UUID
	ReceivedAt time.Time
}

type RFQPage struct {
	Items      []RFQ
	NextCursor *Cursor
}
