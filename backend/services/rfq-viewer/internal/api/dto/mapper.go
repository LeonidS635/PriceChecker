package dto

import "github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/domain"

func FromDomainPage(page domain.RFQPage, clientName string) ClientRFQsPage {
	items := make([]RFQ, 0, len(page.Items))
	for _, item := range page.Items {
		items = append(items, fromDomainRFQ(item, clientName))
	}

	result := ClientRFQsPage{Items: items}
	if page.NextCursor != nil {
		result.NextCursor = &Cursor{
			JobID:      page.NextCursor.JobID.String(),
			ReceivedAt: page.NextCursor.ReceivedAt,
		}
	}

	return result
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
