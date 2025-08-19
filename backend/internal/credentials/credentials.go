package credentials

import (
	_ "embed"
	"encoding/json"
	"log"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
)

//go:embed credentials.json
var rowData []byte

var Credentials map[domain.PortalID]dto.Credentials

func init() {
	if err := json.Unmarshal(rowData, &Credentials); err != nil {
		log.Fatal(err)
	}
	//Credentials = map[domain.PortalID]dto.Credentials{
	//	0: {
	//		Username: "sales@airpartsol.com",
	//		Password: "ABSD2k!",
	//	},
	//	1: {
	//		Username: "",
	//		Password: "",
	//	},
	//	2: {
	//		Username: "",
	//		Password: "",
	//	},
	//	3: {
	//		Username: "",
	//		Password: "",
	//	},
	//}
}
