package main

import (
	"database/sql"
)

func main() { do() }

func do() error {
	db, err := sql.Open("sqlite3", "file:memdb1?mode=memory&cache=shared")
	if err != nil {
		return err
	}
	defer db.Close()

	// START OMIT
	rows, err := db.Query("select * from gophers") // HL
	if err != nil {
		return err
	}
	defer rows.Close() // Don't forget to close! // HL

	for rows.Next() { // HL
		var id int
		var name string
		if err := rows.Scan(&id, &name); err != nil { // HL
			return err
		}
		// ...
		_ = id   // OMIT
		_ = name // OMIT
	}

	if err := rows.Err(); err != nil { // Don't forget to check! // HL
		return err
	}
	// END OMIT
	return nil
}
