package main

import (
	"fmt"
	"iter"
	"log"

	"github.com/achille-roussel/kway-go"
)

func main() {
	// START OMIT
	sequence := func(min, max, step int) iter.Seq2[int, error] {
		return func(yield func(int, error) bool) {
			for i := min; i < max; i += step {
				if !yield(i, nil) {
					return
				}
			}
		}
	}

	// START LOOP OMIT
	for value, err := range kway.Merge( // HL
		sequence(0, 5, 1), // 0,1,2,3,4
		sequence(1, 5, 2), // 1,3
		sequence(2, 5, 3), // 2
	) {
		if err != nil {
			log.Fatal(err)
		}
		fmt.Printf("%d,", value)
	}
	// END OMIT
}
