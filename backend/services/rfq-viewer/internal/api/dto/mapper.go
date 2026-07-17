package dto

import (
	"encoding/base64"
	"encoding/json"
	"fmt"

	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/domain"
	"github.com/google/uuid"
)

// ==== Page =======================

func FromDomainPage(page domain.RFQPage, clientName string) ClientRFQsPage {
	items := make([]RFQ, 0, len(page.Items))
	for _, item := range page.Items {
		items = append(items, fromDomainRFQ(item, clientName))
	}
	cursor := FromDomainCursor(page.NextCursor)
	pagination := FromCursorToPagination(cursor)

	return ClientRFQsPage{Items: items, Pagination: pagination}
}

func fromDomainRFQ(item domain.RFQ, clientName string) RFQ {
	return RFQ{
		ClientName: clientName,
		Subject:    item.Subject,
		ReceivedAt: item.ReceivedAt,
		Parts:      fromDomainParts(item.Parts),
	}
}

func fromDomainParts(parts []domain.Part) []Part {
	result := make([]Part, 0, len(parts))
	for _, part := range parts {
		result = append(result, Part{
			PartNumber:   part.PartNumber,
			Description:  part.Description,
			Quantity:     part.Quantity,
			Alternatives: part.Alternatives,
		})
	}

	return result
}

// ==== Cursor =====================

func FromDomainCursor(cursor *domain.Cursor) *Cursor {
	if cursor == nil {
		return nil
	}
	return &Cursor{
		ReceivedAt: cursor.ReceivedAt,
		JobID:      cursor.JobID.String(),
		PartID:     cursor.PartID,
	}
}

func ToDomainCursor(cursor *Cursor) *domain.Cursor {
	if cursor == nil {
		return nil
	}
	return &domain.Cursor{
		ReceivedAt: cursor.ReceivedAt,
		JobID:      uuid.MustParse(cursor.JobID),
		PartID:     cursor.PartID,
	}
}

// ==== Pagination =================

func FromCursorToPagination(cursor *Cursor) Pagination {
	if cursor == nil {
		return Pagination{HasNext: false}
	}

	encoded, _ := json.Marshal(cursor)
	return Pagination{
		HasNext: true,
		Next:    base64.RawURLEncoding.EncodeToString(encoded),
	}
}

func FromPaginationToCursor(after string) (*Cursor, error) {
	if after == "" {
		return nil, nil
	}

	decoded, err := base64.RawURLEncoding.DecodeString(after)
	if err != nil {
		return nil, fmt.Errorf("decode cursor: %w", err)
	}

	var cursor Cursor
	if err := json.Unmarshal(decoded, &cursor); err != nil {
		return nil, fmt.Errorf("unmarshal cursor: %w", err)
	}
	return &cursor, nil
}
