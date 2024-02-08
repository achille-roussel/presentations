package main

import (
	"database/sql"
	"log"

	"github.com/achille-roussel/sqlrange"
)

func main() {
	db, err := sql.Open("sqlite3", "file:memdb1?mode=memory&cache=shared")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// START OMIT
	type Gopher struct {
		ID   int    `sql:"id"`
		Name string `sql:"name"`
	}

	for g, err := range sqlrange.Query[Gopher](db, "select * from gophers") { // HL
		if err != nil {
			log.Fatal(err)
		}
		// ...
		_ = g // OMIT
	}
	// END OMIT

}
