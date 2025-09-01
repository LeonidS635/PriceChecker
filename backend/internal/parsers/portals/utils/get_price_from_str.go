package utils

import (
	"strconv"
	"strings"
)

func GetPriceFromString(str string) (float32, error) {
	price, err := strconv.ParseFloat(
		strings.TrimSpace(strings.ReplaceAll(strings.ReplaceAll(str, "$", ""), ",", "")), 32,
	)
	if err != nil {
		return 0, err
	}
	return float32(price), nil
}
