package conditions

import "strings"

type ID int

const (
	Unknown ID = iota
	NS
	NE
	OH
	AS
	SV
)

type Condition struct {
	ID   ID     `json:"id"`
	Code string `json:"code"`
	Name string `json:"name"`
}

var Conditions = []Condition{
	{ID: Unknown, Code: "", Name: "Unknown"},
	{ID: NS, Code: "NS", Name: "New Surplus"},
	{ID: NE, Code: "NE", Name: "New"},
	{ID: OH, Code: "OH", Name: "Overhaul"},
	{ID: AS, Code: "AS", Name: "As Removed"},
	{ID: SV, Code: "SV", Name: "Serviceable"},
}

func GetID(cnd string) ID {
	switch c := strings.ToLower(strings.TrimSpace(cnd)); c {
	case "new surplus", "ns":
		return NS
	case "factory new", "new", "ne":
		return NE
	case "overhaul", "overhauled", "oh":
		return OH
	case "as removed", "as":
		return AS
	case "serviceable", "sv":
		return SV
	default:
		return Unknown
	}
}
