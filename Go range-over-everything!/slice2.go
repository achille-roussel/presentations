package main

import "fmt"

func main() {
	// START OMIT
	for i, word := range []string{"hello", "world", "!"} { // HL
		fmt.Printf("%d: %s\n", i, word)
	}
	// END OMIT
}
