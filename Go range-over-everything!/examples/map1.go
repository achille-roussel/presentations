package main

func main() {
	// START OMIT
	for k := range map[string]int{"one": 1, "two": 2, "three": 3} { // HL
		println(k)
	}
	// END OMIT
}
