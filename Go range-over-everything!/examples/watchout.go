package main

func main() {
	go121()
	go122()
}

func go121() {
	// START 1.21 OMIT
	n := 5
	for i := 0; i < n; i++ { // the value of n is evaluted at each iteration // HL
		n /= 2
		println(i)
	}
	// END 1.21 OMIT
}

func go122() {
	// START 1.22 OMIT
	n := 5
	for i := range n { // the value of n is captured here! // HL
		n /= 2
		println(i)
	}
	// END 1.22 OMIT
}
