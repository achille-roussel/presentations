# Sandboxing DuckDB with io/fs

GopherCon 2026 — Seattle — Thursday, August 6th
Speaker transcript

Conventions: prose is the spoken text. Fenced code blocks are shown on slides
at that point in the talk. `[DIAGRAM: ...]` marks where an architecture
diagram is displayed.

---

## Part 1 — The problem, the solution, and what it unlocks

Hello everyone, thank you all for being here.

My name is Achille, I'm currently the Co-Founder and CTO of Firetiger, where we
develop AI agents that verify the changes you push to production. I've been
using Go since 2014 and authored and contributed to several projects, including
the Go runtime and compiler.

What I'm here to talk to you about today is about more than Go.

We're going to talk about DuckDB. We're going to talk about CGO, and I know
some of you just shivered, stay with me. We're going to talk about io/fs, which
I think is an underrated corner of the standard library. And how we used all
those tools as the fundamental building block in the query engine that our
agents use to access data.

Before we dive in, let me ask: who here has used DuckDB before? Alright, a good
chunk of the room. And who here has shipped CGO to production on purpose? Fewer
hands (or more hands). That's reassuring (or not). I hope that today, we'll all
feel a little better about using CGO, when it matters, because we'll have seen
examples of when to reach out for it, and what to lookout for, with a practical
use case of integrating DuckDB in Go applications.

Let's start with DuckDB.

DuckDB is an embedded SQL database optimized for analytics workloads. The way I
like to describe it is: it's SQLite, but for analytics. Where SQLite stores
rows and is optimized for transactional workloads, DuckDB is columnar,
vectorized, and optimized for scanning and aggregating large amounts of data.
It runs in your process, there's no server, no cluster, no operations. And it's
a real database: full SQL support, inserts, updates, transactions, the whole
thing.

But here's the part that I find the most powerful, and it's not the database
part at all. DuckDB can query almost anything. You can point it at a CSV file
and select from it. You can point it at JSON. You can point it at Parquet files
and it will read the metadata, use the column statistics, and only fetch the
pages it needs. And that's just the built-in formats.

```sql
SELECT * FROM read_csv('records.csv');

SELECT * FROM read_json('events.json');

SELECT * FROM read_parquet('s3://bucket/table/*.parquet');
```

Then there's the extension ecosystem, and this is where it gets a little bit
crazy. There are extensions to query files over HTTP, on S3, on GCS. There are
extensions to connect to Postgres, to ClickHouse, to Iceberg tables. And
because it's all SQL, you can join across all of these in a single query. You
can join a Parquet file on S3 with a Postgres table and a CSV file on your
laptop, in one statement.

Under the hood, DuckDB builds one logical query plan, and then maps it to a
physical plan for each data source, pushing predicates down whenever the source
supports it. So when you filter on a column, that filter travels as close to
the data as possible. This is decades of database research and engineering,
definitely not the kind of things we want to rewrite. It is an extremely
powerful piece of software, and it's free, and it's open-source. But it's
written in C++!

So what are we using it for?

Our agents verify changes that engineers ship to production, they do this by
emitting tool calls to query telemetry like logs, metrics, traces... and DuckDB
is the building block for the underlying query engine. The data itself lives in
Apache Iceberg tables: think of Iceberg as a way to lay out Parquet files on an
object store so they behave like logical tables. That's all we need to know
about it for this talk.

Now, one thing we've all learned over the last couple of years is that agents
are really, really good at generating SQL. Give a model a schema and a
question, and it will write you a query to explore the data set. So SQL became
the interface between our agents and our customers' telemetry. And that means
we needed a query engine that could execute arbitrary SQL against tables on
object storage, embedded in our own infrastructure.

That's exactly what DuckDB is great at. But here's the important nuance: we use
DuckDB as a query engine only. We don't use the database part of it at all. We
don't store anything in DuckDB. The data lives in the object store, DuckDB just
executes queries against it and produces results.

And this is where DuckDB is really versatile: it favors composability. You can
pick and choose the pieces you want. Our Go application is an RPC service; it
handles authentication, it configures the query context, it does
instrumentation, rate limiting, all the things a service does. DuckDB is just
the engine sitting inside it, executing the query against the data.

[DIAGRAM: RPC service architecture — incoming request flows through
authentication, configuration, and instrumentation layers in the Go
application; DuckDB sits embedded at the center as the query engine; data
sources (object storage) on the right]

A quick practical note on how we build this, because people always ask. DuckDB
is distributed as a C++ library, and we use pixi, a package manager from the
conda ecosystem, to install a pre-built libduckdb in our Docker images. We link
dynamically, and because it happens inside a Docker build, it's fully
deterministic. Dynamic linking here is just a pragmatic choice: it keeps
compilation fast and avoids the build-time pain of compiling a large C++
project inside every Go build. On the Go side it's one environment variable to
point CGO at the library, and one build tag to tell the bindings to use it.
That's the whole setup.

```dockerfile
FROM ghcr.io/prefix-dev/pixi:latest AS pixi
WORKDIR /src
COPY pixi.toml pixi.lock .
RUN pixi install --locked

FROM golang:1.25 AS build
WORKDIR /src
COPY --from=pixi /src/.pixi .pixi
COPY . .
ENV CGO_LDFLAGS="-L/src/.pixi/envs/default/lib -lduckdb"
RUN go build -tags=duckdb_use_lib
```

Alright. So we embedded a C++ query engine in a Go service. What could possibly
go wrong?

Let me open a parenthesis on CGO first, because I can hear some of you thinking
it.

In the Go ecosystem, we have a strong tendency to rewrite everything in Go. And
I'm as guilty of this as anyone, I literally rewrote Parquet in Go, there's a
whole talk about it. That used to be a bold move. And nowadays, with LLMs
writing a lot of the code, rewriting has never been cheaper. The bar for
"should we just rewrite this in Go" has genuinely moved.

But it hasn't moved infinitely. There are still pieces of software that cross
the threshold where reusing beats rewriting, and a query engine like DuckDB is
firmly on the other side of that line. There are decades of query optimization
research in there, thousands of contributors, an enormous test surface, and a
level of maturity you do not regenerate with a prompt. Not every great piece of
software can be written in Go, and that's fine. For DuckDB, embedding the C++
code through CGO is simply the right call.

Closing the parenthesis. Because even when CGO is the right call, you inherit a
very specific set of problems. And the root of all of them is this: you end up
with two I/O stacks in one binary.

[DIAGRAM: two I/O stacks side by side in one process — left: Go runtime with
goroutines, scheduler, netpoller, net/http, AWS SDK; right: DuckDB C++ stack
with its own thread pool, buffer manager, HTTP client, credential chain; a
wall between them labeled "CGO boundary"]

On one side, the Go runtime manages I/O through the io and net packages. We get
goroutines, we get the scheduler multiplexing them across CPUs, we get the
netpoller. It's a beautiful, coherent world.

On the other side, DuckDB's I/O stack is a whole different beast. It has its
own thread pools, its own buffering, its own HTTP client, its own retry logic.
And now, to understand the behavior or the performance of your service, you
need to understand how those two worlds interact. Trust me, that is not a fun
debugging session.

Speaking of debugging: all the tools we love just stop working at the CGO
boundary. pprof cannot see into the C++ side of the program. Your OpenTelemetry
instrumentation doesn't exist over there. From the Go side, a query is one
giant opaque function call: it enters CGO, time passes, results come out. What
did it read? How many requests did it make to S3? Was the cache warm? You don't
know.

And then there's authentication, which is where this gets genuinely painful.
Our Go application already uses the AWS SDK. Credentials are configured, they
rotate, role assumption works, all of it battle-tested. But DuckDB doesn't know
about any of that. To let it read from S3, you install another extension, and
you configure a whole different HTTP client, with its own credential chain, its
own set of subtle behavior differences, and its own bugs. We had this problem
solved once in our application, and now we have to solve it a second time, in a
different language, inside a library we don't control.

By embedding DuckDB, we inherited a whole bag of problems that Go normally
solves for us out of the box. And I want to emphasize: this is not specific to
us. Every Go application embedding DuckDB, and honestly, every Go application
embedding any C library that does its own I/O, runs into exactly this.

So how did we solve it?

Here's the thing: DuckDB is really well architected. All I/O in DuckDB, every
single file operation, goes through a virtual file system abstraction. There's
a FileSystem base class in the C++ code, and everything above it, the Parquet
reader, the CSV reader, the buffer manager, only talks to that interface. By
default, DuckDB is compiled with an implementation that uses the local file
system. Extensions like httpfs work by plugging alternative implementations
into that same abstraction.

And when I saw that, I thought to myself: wait. If httpfs can inject a file
system, can I write my own virtual file system, and use CGO to inject Go into
it?

Because Go also has an abstraction for virtual file systems. It's the io/fs
package, added in Go 1.16, and at its center is the fs.FS interface. And I love
this interface, it's one method: Open takes a name, returns a file. That's it.

```go
type FS interface {
	Open(name string) (File, error)
}

type File interface {
	Stat() (FileInfo, error)
	Read([]byte) (int, error)
	Close() error
}
```

The standard library gives you implementations for free: os.DirFS for a real
directory, embed.FS for files compiled into your binary, fstest.MapFS for
in-memory testing. And half the ecosystem already implements it.

Now, fs.FS is read-only. There's no Write in the interface. But remember, we
use DuckDB as a query engine only. We never write. Read-only is not a
limitation for us, it's actually exactly the contract we want.

So that's what we built, and it's open-source:
github.com/firetiger-oss/go-duckfs. The package lets you mount any fs.FS as the
virtual file system backing a DuckDB database.

Here is what using it looks like.

```go
c, err := duckfs.Open("", nil, os.DirFS("testdata"))
if err != nil {
	log.Fatal(err)
}

db := sql.OpenDB(c)
defer db.Close()

rows, err := db.Query(`SELECT * FROM read_parquet('data.parquet')`)
```

You call duckfs.Open, and you hand it a file system, here os.DirFS of a data
directory. You get back a connector, you pass that to sql.OpenDB, and from here
on, it's just database/sql, the standard interfaces you already know. When
DuckDB opens data.parquet, it's not touching the operating system. It's calling
your fs.FS.

And the paths are just strings, so they can be anything your file system
understands. You can register a file system that handles paths like
"s3://bucket/table/file.parquet", and DuckDB will happily pass the whole thing
to your Open method.

[DIAGRAM: the bridge at a high level — DuckDB (C++) at the top, its virtual
file system layer below it, the go-duckfs extension crossing the CGO boundary,
and the fs.FS implementation at the bottom fanning out to os.DirFS, S3 client,
GCS client, in-memory maps]

In the second part of this talk I'll walk you through exactly how this bridge
is implemented, but first let me spend a minute on why it was worth building,
because the benefits go quite a bit further than fixing the problems we just
listed.

First, sandboxing, it's in the title of the talk. Every single I/O operation
DuckDB performs now goes through an interface we control. DuckDB cannot open a
socket, cannot read a file, cannot touch anything we didn't explicitly hand it.
If the file system we mount only exposes one customer's data, then that query,
no matter what SQL the agent generated, can only ever read that customer's
data. The sandbox isn't a policy we check, it's a structural property of the
program. And when your queries are written by AI agents, let me tell you, that
property helps you sleep at night.

Second, observability. Every byte DuckDB reads now flows through Go code, which
means we can instrument all of it with the same tools as the rest of the
application. Every file operation DuckDB performs gets attached to the
OpenTelemetry trace of the request that triggered it, so when a query is slow,
we see exactly why: cache misses, poor pushdown, an authentication error three
layers down. I'll show you exactly how we wire the tracing context through in
the third part of the talk.

Third, virtualization means we can plug in any backend. When DuckDB asks for
"s3://" something, our Open method sees the prefix and picks the AWS client;
"gs://", the GCS client. And these are the same client instances the rest of
the application already uses. Same credentials, same configuration, same
connection pools, same retry logic. That painful "configure authentication
twice" problem? Just gone.

Fourth, performance. Because the file system is just a value, we can wrap it.
We inject a caching layer between DuckDB and object storage, page-cache style,
shared across queries. That's a plain fs.FS wrapper, ordinary Go code,
unit-testable, instrumented like everything else.

Fifth, testing. The standard library ships fstest.MapFS, an in-memory fs.FS
built from a map. So in our tests, we craft a map of files in Go, mount it, and
run a full DuckDB query engine against it. No fixtures on disk, no Docker, no
network. Testing an embedded C++ database with a map literal. It's delightful.

And finally, security in a broader sense. Think about what's left running as
C++ in this design: pure computation over in-memory data. All I/O, including
TLS, certificate validation, credential handling, happens in Go, in the same
code paths as the rest of the application, in a memory-safe language. The C++
attack surface shrinks down to, essentially, pure functions.

One small package. All the CGO integration problems we listed, solved. Plus
capabilities we didn't have before.

---

## Part 2 — Inside go-duckfs

Alright, now let's get into the juicy stuff: how do you actually build this?
The whole bridge is under a thousand lines of code, and it has exactly two
pieces: a small C++ extension, and a set of exported Go functions. Let me walk
you through both.

### The shape of the DuckDB virtual file system API

First, we need to understand what we're plugging into. DuckDB's virtual file
system is a C++ class, and a simplified view of it looks like this.

```cpp
class FileSystem {
public:
	virtual unique_ptr<FileHandle> OpenFile(const string &path,
	                                        FileOpenFlags flags,
	                                        optional_ptr<FileOpener> opener);

	virtual void Read(FileHandle &handle, void *buffer,
	                  int64_t nr_bytes, idx_t location);

	virtual int64_t GetFileSize(FileHandle &handle);

	virtual bool FileExists(const string &filename,
	                        optional_ptr<FileOpener> opener);

	virtual vector<OpenFileInfo> Glob(const string &path,
	                                  FileOpener *opener);

	// ... and about twenty more virtual methods
};
```

It's a classic object-oriented design: OpenFile returns a FileHandle, and then
reads, seeks, stats all take that handle. Glob is in there too, because when
you query "star dot parquet", someone has to expand that pattern. DuckDB lets
you register any number of these file systems as subsystems, and routes each
path to the one that claims it. That's exactly how httpfs works.

Now here's the first problem. This API is C++ only. Virtual methods, templates,
unique_ptr, std::string. And CGO does not speak C++. CGO can only call plain C
functions. DuckDB does ship a C API, the duckdb.h header that the Go bindings
are built on, but the virtual file system is not part of it. There is no C API
for file systems.

So the bridge has to be a C++ class. We implement a subclass of
duckdb::FileSystem, called GoFileSystem, and its only job is to translate every
virtual method call into a plain C function call, because plain C functions are
exactly the thing that Go can provide.

[DIAGRAM: the three-layer bridge — DuckDB core calls virtual methods on
GoFileSystem (C++); GoFileSystem calls plain extern "C" functions
(duckfs_file_open, duckfs_file_read_at, ...); those functions are implemented
in Go with //export and call into the fs.FS]

On the C++ side, we declare the C functions we wish existed.

```cpp
extern "C" {
	int     duckfs_file_open(int id, const char *path);
	int64_t duckfs_file_size(int id);
	int64_t duckfs_file_read_at(int id, void *buf,
	                            int64_t size, int64_t off);
	int     duckfs_file_close(int id);
	char   *duckfs_glob(int id, const char *pattern);
	// ...
}
```

And each method of GoFileSystem is a one-liner that forwards to one of them,
plus error translation, because DuckDB reports errors with C++ exceptions and
our C functions report them with negative return values.

```cpp
class GoFileSystem : public FileSystem {
	void Read(FileHandle &handle, void *buf,
	          int64_t size, idx_t off) override {
		auto f = dynamic_cast<GoFileHandle*>(&handle);
		auto n = duckfs_file_read_at(f->id, buf, size, off);
		if (n < 0) {
			throw IOException("failed to read: " + handle.GetPath());
		}
	}
	// every other method looks just like this
};
```

Where do those C functions come from? This is my favorite part of CGO, and it's
the part people use the least: it goes both ways. Everyone knows Go can call C.
But with the //export directive, C can call Go. You write a Go function, you
put //export and its name in a comment above it, and the Go toolchain generates
a C symbol for it that any C or C++ code in the binary can call.

Here's the Go side of the read operation we just saw.

```go
//export duckfs_file_read_at
func duckfs_file_read_at(id C.int, buf unsafe.Pointer,
	size, off C.int64_t) C.int64_t {

	f, ok := globalFiles.lookup(int32(id))
	if !ok {
		return -1
	}
	r, ok := f.(io.ReaderAt)
	if !ok {
		return -1
	}
	buffer := unsafe.Slice((*byte)(buf), size)
	n, err := r.ReadAt(buffer, int64(off))
	if err != nil && n == 0 {
		return -1
	}
	return C.int64_t(n)
}
```

Look at what happens here: DuckDB hands us a pointer to its own buffer, and
unsafe.Slice wraps it as a Go byte slice, no copy. We call ReadAt on the fs.File
and the data lands directly in DuckDB's memory. The whole crossing costs one
function call and zero allocations.

There's one more piece of plumbing: registration. When you create a connector,
we need to tell the DuckDB instance "here is a new file system subsystem". The
C API gives us an opaque duckdb_database handle, and our extension casts it
back to the internal C++ wrapper to reach the FileSystem registry.

```cpp
duckdb_state duckfs_register_subsystem(duckdb_database database, int id) {
	auto wrapper = reinterpret_cast<duckdb::DatabaseWrapper *>(database);
	auto &fs = duckdb::FileSystem::GetFileSystem(
		*wrapper->database->instance.get());
	fs.RegisterSubSystem(duckdb::make_uniq<duckdb::GoFileSystem>(id));
	return DuckDBSuccess;
}
```

Is reaching through the C API's opaque pointer into internal C++ types a little
bold? Yes. But this is the kind of decision you get to make when you own the
glue layer: we pin the DuckDB version in our build anyway, so this is a
controlled risk, checked by tests.

### Retaining Go objects across the boundary

Now, you may have noticed something in all the code I've shown so far: there is
not a single Go pointer crossing into C++. Everything is done with these little
integer IDs. That's not an accident, and it's the second implementation
challenge I want to talk about, because anyone who bridges Go with C will hit
it.

Here's the constraint. The natural design would be: open a file, hand C++ a
pointer to the fs.File, and have every read pass that pointer back. But the
CGO pointer passing rules say no. C memory must not hold Go pointers across
calls: the garbage collector can't see into C++, so it wouldn't know the object
is still referenced, and nothing keeps it alive. These rules exist so the
runtime keeps its freedom, and today's collector already moves goroutine
stacks; you don't want to be the program that breaks when it starts moving your
heap.

So instead of passing pointers out, we keep every Go object at home, in a
registry, and we hand C++ a claim ticket.

```go
type filemap[T comparable] struct {
	mutex sync.RWMutex
	files []T
}

func (m *filemap[T]) register(f T) int32        // store, get an id
func (m *filemap[T]) lookup(id int32) (T, bool) // resolve an id
func (m *filemap[T]) unregister(id int32) (T, bool)

var (
	globalFsys  filemap[fs.FS]   // mounted file systems
	globalFiles filemap[fs.File] // open files
)
```

[DIAGRAM: handle registry — C++ side holds only integers (fsys id 0, file ids
3, 7, 12); Go side holds the registry slices mapping those ids to live fs.FS
and fs.File values; arrows showing lookup on each call crossing the boundary]

Two registries: one for the mounted file systems, one for open files. When
DuckDB opens a file, we register the fs.File and return its index. Every
subsequent operation carries that integer, and the trampoline looks the object
up again. When the file closes, we unregister it, and from that point the
object is garbage like any other Go value. The registry is the only thing
keeping these objects alive, which means the lifetime of Go objects is
explicitly tied to the lifetime of DuckDB's file handles. The mutex makes it
safe to call from any thread, and that matters because DuckDB will call us from
its own worker threads, not from a goroutine.

And that's really all there is to the core of the bridge: a C++ class that
turns virtual calls into C calls, exported Go functions that turn C calls into
interface calls, and an ID registry so no pointer ever crosses the line. Under
a thousand lines, total.

---

## Part 3 — Usability: propagating context.Context

So at this point we have a working bridge, and if all you need is to query
local, static data, you're done. But the moment we put this in production, we
hit a usability problem that I think is the most instructive part of the whole
project: context.

Think about what our service does. An RPC comes in. It carries a
context.Context, and that context carries everything: the deadline, the
cancellation signal, the tenant identity, the OpenTelemetry span. Every I/O
operation we perform on behalf of that request is supposed to flow through that
context. That's the contract of a well-behaved Go service.

Now trace the path of a read. The request handler executes a SQL query. The
query descends into DuckDB, into C++. DuckDB schedules work on its own worker
threads, and somewhere down there, a Parquet reader asks for bytes, and the
call comes back up into our Go code through the bridge. And what do we receive?

```go
func (fsys *fileSystem) Open(name string) (fs.File, error)
```

A string. fs.FS knows nothing about context, the interface is deliberately
minimal. And there's no goroutine-local magic to save us either: this call
isn't even coming from the goroutine that ran the query, it's coming from a
DuckDB worker thread. The context is gone.

[DIAGRAM: the context gap — request ctx enters the handler goroutine, crosses
into C++ where DuckDB fans out to worker threads, and re-enters Go via the
bridge on a different thread with no ctx; a dotted line shows the path the
context needs to travel]

So how do we get the request's context back on the other side of a C++ thread
pool?

The answer is a pattern you've already seen once in this talk: the file system
is just a value, and values can capture things. When the request arrives, we
construct the fs.FS for that specific request, and we store the context inside
it.

```go
// FS binds the storage registry to the context of one request.
func FS(ctx context.Context, reg Registry) fs.FS {
	return &fileSystem{ctx: ctx, reg: reg}
}

type fileSystem struct {
	ctx context.Context
	reg Registry
}

func (fsys *fileSystem) Open(name string) (fs.File, error) {
	bucket, key, err := resolve(fsys.ctx, fsys.reg, name)
	if err != nil {
		return nil, &fs.PathError{Op: "open", Path: name, Err: err}
	}
	return &file{ctx: fsys.ctx, bucket: bucket, key: key}, nil
}
```

Open re-injects the captured context into everything it does: resolving the
bucket, authenticating, and the file it returns carries the context too, so
every ReadAt turns into an object store request made with the request's
context. Deadline, cancellation, tracing span: they all made it across the C++
thread pool, because they were smuggled inside the file system value itself.

Now, I know what some of you are thinking, because it's written in the context
package documentation: "do not store a context inside a struct type". And as a
general rule, that's right. But notice why the rule exists: a context stored in
a long-lived object outlives the request it belongs to. Here, the file system
value IS the request-scoped object. It's created when the query starts, it's
used by the query, and it dies with the query. The lifetime of the struct and
the lifetime of the context are the same, which is exactly the situation where
capturing it is correct. This is the escape hatch the guideline leaves open,
and crossing a foreign thread pool is precisely what it's for.

There's one last wrinkle, and it comes from performance. Creating a DuckDB
connector is expensive, so we don't create one per request, we pool instances
and reuse them. But the file system is registered with DuckDB once, when the
connector is created. So how do we swap in a per-request file system on a
pooled instance?

With one more layer of indirection: the file system we actually mount is a
tiny resettable wrapper, and each query points it at the current request's
context-bound file system.

```go
type duckDBFileSystem struct{ fsys fs.FS }

func (d *duckDBFileSystem) Open(name string) (fs.File, error) {
	if d.fsys == nil {
		return nil, fs.ErrNotExist
	}
	return d.fsys.Open(name)
}

func (d *duckDBFileSystem) Reset(fsys fs.FS) { d.fsys = fsys }
```

```go
func (p *Pool) Query(ctx context.Context, registry storage.Registry,
	sql string, args ...any) (array.RecordReader, error) {

	db := p.get() // pooled instance, created with duckfs.Open(...)

	fsys := storage.FS(ctx, registry) // capture this request's context
	db.fileSystem.Reset(fsys)         // mount it for this query

	// ... run the query, return the instance to the pool when done
}
```

When the query finishes, we reset the wrapper to nil and put the instance back
in the pool. The context never leaks past its request, and the pooled DuckDB
instance never holds onto anything request-scoped between queries.

[DIAGRAM: end-to-end flow with pooling — request ctx → storage.FS(ctx) →
Reset on the pooled instance's wrapper FS → DuckDB worker threads → Open/Read
re-enter Go → object store clients called with the original ctx → spans
attached to the request trace]

And this is what the payoff looks like: one trace, end to end. The incoming
RPC at the top, the SQL query below it, and then every single object store
read that DuckDB triggered, each with its timing, each with its result,
hanging off the request's span. When a query is slow, we don't guess anymore.
We look.

[DIAGRAM: screenshot-style trace waterfall — RPC span at top, query span
below, dozens of object store GET spans underneath with varying durations,
one highlighted showing an authentication error]

---

## Takeaways

So let me leave you with three takeaways.

First, on software design. In the age of LLMs, I think we tend to overlook how
much good design matters. The bar for what should be rewritten versus reused
has moved, no question. But there are still high-quality pieces of software out
there that we should reuse, and when we do, investing in the glue layer is
where the leverage is. DuckDB exposing a virtual file system abstraction, and
Go shipping fs.FS in the standard library, is what made a one-thousand-line
bridge possible. That's not luck, that's two well-designed systems meeting in
the middle. And the pattern generalizes: most serious C libraries that do I/O
expose some virtual file system hook. SQLite has one. If you can connect that
hook to io/fs, everything I showed you today applies.

Second, the implementation techniques we covered are the reusable part: a thin
C++ class to translate an object-oriented API into plain C functions, //export
to let C call Go, integer handles instead of pointers so the garbage collector
stays free, and request-scoped values to carry context across a foreign thread
pool. That toolbox works for far more than DuckDB.

And third, I hope you walk away with a more refined sense of when CGO is the
right tool. Not "never", not "whatever", but: know the problems you're signing
up for, the two I/O stacks, the observability wall, the duplicated
configuration, and know that with the right abstraction at the boundary, you
can make most of them disappear.

Everything I showed today is open-source at github.com/firetiger-oss/go-duckfs.
It's MIT licensed, issues and contributions are very welcome, there's plenty
left to build. And as always, remember to support your open-source maintainers
by being generous with GitHub stars.

Thank you GopherCon! I think we have a couple of minutes for questions.
