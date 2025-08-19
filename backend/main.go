package main

import (
	"context"
	"log"

	"github.com/LeonidS635/PriceChecker/backend/internal/server"
)

func main() {
	ctx := context.Background()
	log.Fatalln(server.StartUpServer(ctx, ":8081"))
}
