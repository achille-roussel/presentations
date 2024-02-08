package main

import "fmt"

func main() {
	// START OMIT
	for i, c := range "Hello, 世界" { // HL
		fmt.Printf("%d: %c\n", i, c)
	}
	// END OMIT
}
