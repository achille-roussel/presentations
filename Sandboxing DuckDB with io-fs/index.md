# Sandboxing DuckDB with io/fs

Introduction - who am I?
- Go since 2014 - contributor
- Co-Founder and CTO of Firetiger
- Author and maintainer of parquet-go
- more OSS

What are we going to talk about?
- DuckDB
- CGO
- io/fs => not well-known part of stdlib
- virtual file systems
- embedded databases
- practical use cases
- open-source
  
What is DuckDB?
- embedded SQL database optimized for analytics workloads (e.g., columnar data formats)
- full SQL support, inserts, updates, transactions
- even tho it's optimized for most powerful is DuckDB can query so many file formats
- CSV, JSON, Parquet (examples of duckdb queries)
- can do even more, huge ecosystem of extensions
- remote queries on object stores, http APIs, Clickhouse, Postgres
- join across all those datasets
- logical query plan maps physical plan for each source, with predicate pushdown when possible
- extremely powerful

What are we using it for?
- agents are really good at generating SQL to explore data sets
- lots of datasources but in this talk focusing mostly data sets are in iceberg tables on S3 or GCS
- apache iceberg is a specification for data lakes, emerged as the most prominent standard across the industry
- think of apache iceberg as a way to layout parquet files on object store so that you can represent logical tables with schemas, physical partitions, sort orders, etc...
- we're using DuckDB as a query engine only, embedded in a Go application
- we're not using the database part of it
- that's where DuckDB is really versatile, you can pick and choose what you want, it really favors compasability
- the Go application is a RPC service, handles authentication, configuration of the query context, instrumentation, etc... DuckDB is just executing the query against the data and producing the results
- pixi for managing the duckdb installation (show Dockerfile example)
- dynamic linking but because we're in a docker image it's deterministic (just make compilation faster, avoid build-time problems of having to compile C++)
- (show go build tags)

What problems did we face?
- written in C++ (not every great piece of software can be written in Go)
- fortunately or unfortunately we have CGO, and Go bindings github.com/duckdb/duckdb-go
  - open a parenthesis on using CGO here
  - in the Go ecosystem we have a tendency of rewriting everything in Go
  - it was a bold approach in the past, it's really easy to do nowadays with LLMs
  - there are still pieces of software that make sense to reuse
  - a query engine like DuckDB still crosses the threshold of what we should reuse instead of rewriting
  - there's enough complexity, testing, and optimizations that it's much better to use CGO and embed the C code than rewrting
- when embedding a C++ library like DuckDB in Go, the root of the problem is that you end up with two I/O stacks
- the Go runtime manages I/O via the io and net packages, we get concurrency with goroutines, scheduling across CPUs, etc...
- the DuckDB I/O stack on the other hand is a whole different beast, it has its own thread pools, we need to understand how those interact to debug behavior and performance problems
- speaking about debugging, the tools we're used to like pprof just don't work on the C part of the program, neither do application-level instrumentation like using opentelemetry
- authentication becomes a problem as well:
  - Go app already uses the AWS SDK and has credentials configured
  - need to also configure DuckDB
  - installing another extension
  - it's a whole different client, with its own set of subtle behavior differences and bugs
  - we already had this problem solved once in our application and now we need to figure out how to solve it a second time
- by embedding DuckDB, we still inherit a whole bag of new problems that we get solutions for free out-of-the-box when we have a pure Go application
- this is a problem that every Go application using DuckDB will run into

How did we solve for this?
- DuckDB is really well architected, all I/O goes through a virtual file system abstraction
- by default DuckDB is compiled with a version of the virtual file system that uses the local file system
- extensions like httpfs provide alternative implementations to query remote file systems
- I thought to myself: can I write my own virtual file system using CGO to inject by own file system?
- Go standard library also has an abstraction for virtual file system: io/fs package and the fs.FS interface
- read-only, but works for our use-case
- I wanted to be able to mount a fs.FS as the underlying virtual file system that DuckDB uses
- github.com/firetiger-oss/go-duckfs
- (show usage examples)
- (high-level examples of the go-duckfs implementation -> show one function)

What we get out of this?
- we can mount a fs.FS as backend for DuckDB
- read-only, and fully sandboxed, no I/O operations that DuckDB 
- can instrument all I/O performed by DuckDB is captured by the Go application
  - show context.Context technique to propagate the opentelemetry tracing context
  - get end-to-end tracing from the incoming RPC to 
  - extremely detailed view of the behavior of the application, especially useful to track down cache utilization, poor query performance, authentication errors
- virtualization means we can plug any backend
  - remember how we are querying iceberg tables on S3 and GCS
  - the fs.FS.Open method receives "s3://" or "gs://"
  - pick the client
  - automatically inherit the credentials configuration
  - e.g., the aws client used by the application is the same 
- performance optimizations by injecting a caching layer
  - page cache style accelerating queries
- much better testing
  - ingest in-memory implementation of fs.FS (fstest.MapFS)
  - can craft tests in Go and run the query engine against it
- security guarantees
  - reduced C code surface to a minimum of "pure function" code operating on in-memory data only
  - all I/O, including TLS happens on the Go application using the same code than the rest of the application

Takeaways
- In the age of LLMs we tend to overlook the importance of good software design
  - the bar for what code should be regenerated vs reused has moved
  - there are high quality pieces of software out there that we should still reuse
  - when that's the case, investing in building the glue layers to solve for the integration problems is important
  - With one simple package (go-duckfs) we solved for all the limitations, while also unlocking capabilities
- For those of you who didn't know about DuckDB, I hope this gives you an idea of where to start if you ever need to leverage it in your work
- And I hope all of you refined your appreciation for when to consider CGO as the right tool, and what challenges you should lookout for when integrating C or C++ code in Go applications
