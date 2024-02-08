package main

import "fmt"

func main() {
	// START OMIT
	for k, v := range map[string]int{"one": 1, "two": 2, "three": 3} { // HL
		fmt.Printf("%v: %v\n", k, v)
	}
	// END OMIT
}
