package main

func main() { do() }

func do() error {
	// START OMIT
	for v, err := range func(yield func(int, error) bool) { // HL
		for i := range 5 {
			if !yield(i, nil) { // HL
				break
			}
		}
	} {
		if err != nil { // HL
			return err
		}
		println(v)
	}
	// END OMIT
	return nil
}
