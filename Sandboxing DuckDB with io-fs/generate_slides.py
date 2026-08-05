#!/usr/bin/env python3
"""Generate slides.pptx for the GopherCon 2026 talk from slide definitions.

The .pptx imports cleanly into Google Slides (File > Import, or Drive upload
with conversion). Each slide carries the transcript prose as speaker notes.

Usage: python3 generate_slides.py
"""

from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# 16:9 geometry
SLIDE_W = Emu(12192000)
SLIDE_H = Emu(6858000)

# Palette
INK = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x6B, 0x72, 0x80)
ACCENT = RGBColor(0xE8, 0x59, 0x0C)  # firetiger orange
CODE_BG = RGBColor(0x1E, 0x1E, 0x1E)
CODE_FG = RGBColor(0xE6, 0xE6, 0xE6)
BOX_BG = RGBColor(0xF1, 0xF3, 0xF5)
BOX_BD = RGBColor(0xAD, 0xB5, 0xBD)

BODY_FONT = "Arial"
CODE_FONT = "Courier New"


def textbox(slide, x, y, w, h):
    box = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    box.text_frame.word_wrap = True
    return box


def add_title(slide, text, color=INK, size=30):
    box = textbox(slide, 600000, 350000, 11000000, 800000)
    p = box.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = text
    r.font.name = BODY_FONT
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = color
    return box


def add_bullets(slide, items, y=1400000, size=20):
    box = textbox(slide, 600000, y, 11000000, SLIDE_H - y - 400000)
    tf = box.text_frame
    first = True
    for item in items:
        level = 0
        if item.startswith("  "):
            level = 1
            item = item.strip()
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        p.space_after = Pt(10)
        r = p.add_run()
        r.text = ("• " if level == 0 else "– ") + item
        r.font.name = BODY_FONT
        r.font.size = Pt(size if level == 0 else size - 2)
        r.font.color.rgb = INK if level == 0 else MUTED
    return box


def add_code(slide, code, y=1350000, size=14, h=None):
    lines = code.strip("\n").split("\n")
    if h is None:
        h = min(int(len(lines) * size * 17000 + 500000), SLIDE_H - y - 350000)
    shape = slide.shapes.add_shape(1, Emu(700000), Emu(y), Emu(10800000), Emu(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = CODE_BG
    shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = False
    tf.margin_left = Emu(300000)
    tf.margin_right = Emu(300000)
    tf.margin_top = Emu(200000)
    tf.margin_bottom = Emu(200000)
    first = True
    for line in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = line if line else " "
        r.font.name = CODE_FONT
        r.font.size = Pt(size)
        r.font.color.rgb = CODE_FG
    return shape


def add_diagram_placeholder(slide, description, y=1400000, h=None):
    if h is None:
        h = SLIDE_H - y - 400000
    shape = slide.shapes.add_shape(1, Emu(700000), Emu(y), Emu(10800000), Emu(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = BOX_BG
    shape.line.color.rgb = BOX_BD
    shape.line.width = Pt(1)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(400000)
    tf.margin_right = Emu(400000)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "[DIAGRAM] " + description
    r.font.name = BODY_FONT
    r.font.size = Pt(16)
    r.font.italic = True
    r.font.color.rgb = MUTED
    return shape


def add_statement(slide, text, size=40, color=INK, y=2600000):
    box = textbox(slide, 900000, y, 10400000, 1800000)
    p = box.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.name = BODY_FONT
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = color
    return box


def set_notes(slide, notes):
    slide.notes_slide.notes_text_frame.text = notes.strip()


# ---------------------------------------------------------------------------
# Slide definitions. kind: title | section | bullets | code | diagram |
# statement | code2. Every slide gets `notes` from the transcript.
# ---------------------------------------------------------------------------

SLIDES = [
    dict(
        kind="title",
        title="Sandboxing DuckDB with io/fs",
        subtitle="Achille Roussel — Co-Founder & CTO, Firetiger\nGopherCon 2026, Seattle",
        notes="Hello everyone, thank you all for being here.",
    ),
    dict(
        kind="bullets",
        title="whoami",
        bullets=[
            "Co-Founder & CTO of Firetiger",
            "  AI agents that verify the changes you push to production",
            "Go developer since 2014",
            "Contributor to the Go runtime and compiler",
            "Open-source: ksuid, kafka-go, parquet-go, ...",
        ],
        notes="""My name is Achille, I'm currently the Co-Founder and CTO of Firetiger, where we develop AI agents that verify the changes you push to production. I've been using Go since 2014 and authored and contributed to several projects, including the Go runtime and compiler.""",
    ),
    dict(
        kind="bullets",
        title="More than Go",
        bullets=[
            "DuckDB",
            "CGO (stay with me)",
            "io/fs — an underrated corner of the standard library",
            "How they became the building blocks of our query engine",
        ],
        notes="""What I'm here to talk to you about today is about more than Go.

We're going to talk about DuckDB. We're going to talk about CGO, and I know some of you just shivered, stay with me. We're going to talk about io/fs, which I think is an underrated corner of the standard library. And how we used all those tools as the fundamental building block in the query engine that our agents use to access data.

Before we dive in, let me ask: who here has used DuckDB before? Alright, a good chunk of the room. And who here has shipped CGO to production on purpose? Fewer hands (or more hands). That's reassuring (or not). I hope that today, we'll all feel a little better about using CGO, when it matters, because we'll have seen examples of when to reach out for it, and what to lookout for, with a practical use case of integrating DuckDB in Go applications.""",
    ),
    dict(
        kind="bullets",
        title="What is DuckDB?",
        bullets=[
            "Embedded SQL database, optimized for analytics",
            "Columnar, vectorized: built to scan and aggregate",
            "In-process: no server, no cluster, no operations",
            "A real database: full SQL, inserts, updates, transactions",
        ],
        notes="""Let's start with DuckDB.

DuckDB is an embedded SQL database optimized for analytics workloads: columnar, vectorized, built for scanning and aggregating large amounts of data. It runs in your process, there's no server, no cluster, no operations. And it's a real database: full SQL support, inserts, updates, transactions, the whole thing.""",
    ),
    dict(
        kind="code",
        title="DuckDB can query almost anything",
        lang="sql",
        code="""
SELECT * FROM 'records.csv';

SELECT * FROM 'events.json';

SELECT * FROM 's3://bucket/table/*.parquet';
""",
        size=18,
        notes="""But the part I find the most powerful is not the database part at all: DuckDB can query almost anything. Point it at a CSV file and select from it. Point it at JSON. Point it at Parquet files and it will read the metadata, use the column statistics, and only fetch the pages it needs.""",
    ),
    dict(
        kind="bullets",
        title="The extension ecosystem",
        bullets=[
            "Query files over HTTP, on S3, on GCS",
            "Connect to Postgres, ClickHouse, Iceberg tables",
            "Join across all of them in a single SQL statement",
            "One logical plan, predicate pushdown per source",
        ],
        notes="""Then there's the extension ecosystem, and this is where it gets a little bit crazy. There are extensions to query files over HTTP, on S3, on GCS. There are extensions to connect to Postgres, or ClickHouse, or Iceberg tables. And because it's all SQL, you can join across all of these in a single query. You can join a Parquet file on S3 with a Postgres table and a CSV file on your laptop, in one statement.

Under the hood, DuckDB builds one logical query plan, and then maps it to a physical plan for each data source, pushing predicates down whenever the source supports it. So when you filter on a column, that filter travels as close to the data as possible. This is decades of database research and engineering, definitely not the kind of things we want to rewrite. It is an extremely powerful piece of software, and it's free, and it's open-source.""",
    ),
    dict(
        kind="statement",
        title="",
        text="But it's written in C++!",
        notes="""But it's written in C++!""",
    ),
    dict(
        kind="bullets",
        title="Rewrite it in Go?",
        bullets=[
            "We rewrite everything in Go — and coding agents made it cheap",
            "The rewrite-vs-reuse bar has shifted towards rewrite",
            "But: decades of research, optimization, bug fixes, tests",
            "That maturity is not regenerated with a prompt",
            "For DuckDB, CGO is simply the right call",
        ],
        notes="""In the Go ecosystem, we have a strong tendency to rewrite everything in Go. And nowadays with coding agents, rewriting has never been cheaper. The bar for deciding whether rewrite or reuse has shifted even further towards rewrite.

But pieces of software like DuckDB have decades of research, optimization, bug fixes, an enormous test surface — a level of maturity you do not regenerate with a prompt. Not every great piece of software is written in Go, and that's fine. For DuckDB, using CGO is simply the right call today.""",
    ),
    dict(
        kind="diagram",
        title="How are we using DuckDB?",
        diagram=(
            "query path through the system: agent `query` tool call over RPC "
            "-> Go service (authentication, configuration, instrumentation, "
            "caching) -> embedded DuckDB (CGO) -> Iceberg tables (Parquet on "
            "S3/GCS) -> results stream back to the agent"
        ),
        notes="""So, how are we using DuckDB?

To query telemetry like logs, metrics, or traces, we give our agents access to a query engine over RPC via a `query` tool. The query engine is written in Go and where we embed DuckDB.

The service handles authentication and configuration of the DuckDB instances to run against the customer data that the agent operates on behalf of. The Go layer also handles other functions like instrumentation for observability or caching to improve query performance.""",
    ),
    dict(
        kind="statement",
        title="",
        text="What could possibly go wrong?",
        notes="""So we embedded a C++ query engine in a Go service. What could possibly go wrong?

Even if CGO is the right call, we still inherit a bunch of problems.""",
    ),
    dict(
        kind="bullets",
        title="Problem #1: linking",
        bullets=[
            "Static linking: C compiler and linker in every Go build — slow",
            "Dynamic linking: depends on the libduckdb of the host",
            "  version mismatches, missing symbols, runtime failures",
        ],
        notes="""The first problems appear at build time: a Go application is a simple statically linked binary, but it's not necessarily true when you bring CGO to the mix. We have to decide if the C code will be statically or dynamically linked. Using static linking tend to make the build much slower, because the C compiler and linkers get involved, and they are much slower than Go. Dynamic linking on the other hand makes the final program unpredictable and it can fail at runtime due to version mismatches causing missing symbol errors.

Like many of you I'm sure, we're using docker images to distribute software artifacts, and this is also how we solve this problem.""",
    ),
    dict(
        kind="code",
        title="Docker makes dynamic linking deterministic",
        lang="dockerfile",
        code="""
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
""",
        notes="""pixi installs a pre-built libduckdb, pinned by its lock file, in its own image layer. The Go build links against it dynamically with this build tag.

This gives us a best-of-both-worlds model: the installation gets cached in the docker layer to keep the build fast, and we know exactly which version of the library we install, ensuring that we have a deterministic build process.""",
    ),
    dict(
        kind="diagram",
        title="Two I/O stacks in one binary",
        diagram=(
            "side by side in one process — left: Go runtime with goroutines, "
            "scheduler, netpoller, net/http, AWS SDK; right: DuckDB C++ stack "
            "with its own thread pool, buffer manager, HTTP client, credential "
            "chain; a wall between them labeled 'CGO boundary'"
        ),
        notes="""That took care of the build problems, but we ran into several other issues, mostly caused by having two I/O stacks within the program.

On one side, the Go runtime manages I/O through the io and net packages. We get goroutines, we get the scheduler multiplexing them across CPUs, we get the netpoller. It's a beautiful, coherent world.

On the other side, DuckDB's I/O stack is a whole different beast. It has its own thread pools, its own buffering, its own HTTP client, its own retry logic. And now, to understand the behavior or the performance of your service, you need to understand how those two worlds interact. Trust me, that is not a fun debugging session.""",
    ),
    dict(
        kind="bullets",
        title="Debugging blind",
        bullets=[
            "pprof stops at the CGO boundary",
            "OpenTelemetry instrumentation doesn't exist in C++",
            "A query = one giant opaque function call",
            "What did it read? How many S3 requests? Cache warm?",
        ],
        notes="""Speaking of debugging: all the tools we love just stop working at the CGO boundary. pprof cannot see into the C++ side of the program. Your OpenTelemetry instrumentation doesn't exist over there. From the Go side, a query is one giant opaque function call: it enters CGO, time passes, results come out, and we have no idea of what happened underneath.""",
    ),
    dict(
        kind="bullets",
        title="Authentication, twice",
        bullets=[
            "The Go app already uses the AWS SDK: rotation, roles, battle-tested",
            "DuckDB knows nothing about it",
            "Another extension, another HTTP client, another credential chain",
            "Same problem, solved twice, in a library we don't control",
        ],
        notes="""And then there's authentication, which is where this gets genuinely painful. Our Go application already uses the AWS SDK. Credentials are configured, they rotate, role assumption works, all of it battle-tested. But DuckDB doesn't know about any of that. To let it read from S3, you install another extension, and you configure a whole different HTTP client, with its own credential chain, its own set of subtle behavior differences, and its own bugs. We had this problem solved once, and now we have to solve it a second time, in a different language, inside a library we don't control.

By embedding DuckDB, we inherited a whole bag of problems that Go normally solves for us out of the box. And this is not specific to DuckDB: every Go application embedding a C library that does its own I/O runs into exactly this.""",
    ),
    dict(
        kind="bullets",
        title="DuckDB's virtual file system",
        bullets=[
            "Every file operation goes through a FileSystem abstraction",
            "Parquet reader, CSV reader, buffer manager: all above it",
            "httpfs = an alternative FileSystem implementation",
            "If httpfs can inject a file system... can I inject Go?",
        ],
        notes="""So how did we solve it?

Here's the thing: DuckDB is really well architected. All I/O in DuckDB, every single file operation, goes through a virtual file system abstraction. There's a FileSystem base class in the C++ code, and everything above it, the Parquet reader, the CSV reader, the buffer manager, only talks to that interface. Extensions like httpfs work by plugging alternative implementations into that same abstraction.

And when I saw that, I thought to myself: wait. If httpfs can inject a file system, can I write my own virtual file system, and use CGO to inject Go into it?""",
    ),
    dict(
        kind="code",
        title="io/fs: Go's virtual file system",
        lang="go",
        code="""
type FS interface {
	Open(name string) (File, error)
}

type File interface {
	Stat() (FileInfo, error)
	Read([]byte) (int, error)
	Close() error
}
""",
        size=16,
        notes="""Because Go also has an abstraction for virtual file systems. It's the io/fs package, added in Go 1.16, and at its center is the fs.FS interface. And I love this interface, it's one method: Open takes a name, returns a file. That's it.

The standard library gives you implementations for free: os.DirFS for a real directory, embed.FS for files compiled into your binary, fstest.MapFS for in-memory testing. And half the ecosystem already implements it.

Now, fs.FS is read-only. There's no Write in the interface. But remember, we use DuckDB as a query engine only. We never write. Read-only is not a limitation for us, it's actually exactly the contract we want.""",
    ),
    dict(
        kind="code",
        title="github.com/firetiger-oss/go-duckfs",
        lang="go",
        code="""
c, err := duckfs.Open("", nil, os.DirFS("testdata"))
if err != nil {
	log.Fatal(err)
}

db := sql.OpenDB(c)
defer db.Close()

rows, err := db.Query(`SELECT * FROM read_parquet('data.parquet')`)
""",
        size=15,
        notes="""So that's what we built, and it's open-source: github.com/firetiger-oss/go-duckfs. The package lets you mount any fs.FS as the virtual file system backing a DuckDB database.

You call duckfs.Open, and you hand it a file system, here os.DirFS of a data directory. You get back a connector, you pass that to sql.OpenDB, and from here on, it's just database/sql, the standard interfaces you already know. When DuckDB opens data.parquet, it's not touching the operating system. It's calling your fs.FS.

And the paths are just strings, so they can be anything your file system understands. You can register a file system that handles paths like "s3://bucket/table/file.parquet", and DuckDB will happily pass the whole thing to your Open method.""",
    ),
    dict(
        kind="diagram",
        title="The bridge",
        diagram=(
            "DuckDB (C++) at the top, its virtual file system layer below it, "
            "the go-duckfs extension crossing the CGO boundary, and the fs.FS "
            "implementation at the bottom fanning out to os.DirFS, S3 client, "
            "GCS client, in-memory maps"
        ),
        notes="""I'll walk you through exactly how this bridge is implemented in a minute, but first: what did it buy us?""",
    ),
    dict(
        kind="bullets",
        title="What it buys us",
        bullets=[
            "Sandboxing: DuckDB can only touch what we hand it",
            "Observability: every byte traced with the request",
            "Any backend: s3://, gs://, same clients, same credentials",
            "Caching: wrap the fs.FS with a page cache, in plain Go",
            "Testing: full engine against fstest.MapFS, no fixtures",
            "Security: C++ reduced to pure compute, all I/O in Go",
        ],
        notes="""First, sandboxing, it's in the title of the talk. Every I/O operation DuckDB performs now goes through an interface we control. DuckDB cannot open a socket, cannot read a file, cannot touch anything we didn't explicitly hand it. If the file system we mount only exposes one customer's data, then no matter what SQL the agent generated, the query can only ever read that customer's data. The sandbox isn't a policy we check, it's a structural property of the program. And when your queries are written by AI agents, that property helps you sleep at night.

Second, observability. Every byte DuckDB reads now flows through Go code, so we can instrument all of it with the same tools as the rest of the application: every file operation gets attached to the OpenTelemetry trace of the request that triggered it. When a query is slow, we see exactly why. I'll show you how we wire the context through in part three.

And it keeps going. Any backend: when Open sees "s3://" it picks the AWS client, "gs://" the GCS client — the same clients, credentials, and retry logic the rest of the application already uses, so the double-authentication problem just disappears. Caching: the file system is a value, so we wrap it with a page-cache layer, in plain Go. Testing: mount an fstest.MapFS and run a full DuckDB engine against a map literal, no fixtures, no Docker, no network. And security: what's left running as C++ is pure computation over in-memory data — all I/O, including TLS and credential handling, happens in memory-safe Go.

One small package. All the CGO integration problems we listed, solved. Plus capabilities we didn't have before.""",
    ),
    dict(
        kind="section",
        title="Part 2 — Inside go-duckfs",
        notes="""Alright, now let's get into the juicy stuff: how do you actually build this? The whole bridge is under a thousand lines of code, and it has exactly two pieces: a small C++ extension, and a set of exported Go functions.""",
    ),
    dict(
        kind="code",
        title="What we're plugging into (C++)",
        lang="cpp",
        code="""
class FileSystem {
public:
	virtual unique_ptr<FileHandle> OpenFile(const string &path,
	                                        FileOpenFlags flags,
	                                        optional_ptr<FileOpener> opener);

	virtual void Read(FileHandle &handle, void *buffer,
	                  int64_t nr_bytes, idx_t location);

	virtual int64_t GetFileSize(FileHandle &handle);

	virtual vector<OpenFileInfo> Glob(const string &path,
	                                  FileOpener *opener);

	// ... and about twenty more virtual methods
};
""",
        size=13,
        notes="""First, we need to understand what we're plugging into. DuckDB's virtual file system is a C++ class, and a simplified view of it looks like this.

Classic object-oriented design: OpenFile returns a FileHandle, and reads, seeks, stats all take that handle. Glob is in there too, because when you query "star dot parquet", someone has to expand that pattern. DuckDB lets you register any number of these file systems as subsystems, and routes each path to the one that claims it. That's exactly how httpfs works.""",
    ),
    dict(
        kind="diagram",
        title="CGO does not speak C++",
        diagram=(
            "the three-layer bridge — DuckDB core calls virtual methods on "
            "GoFileSystem (C++); GoFileSystem calls plain extern \"C\" "
            "functions (duckfs_file_open, duckfs_file_read_at, ...); those "
            "functions are implemented in Go with //export and call into the "
            "fs.FS"
        ),
        notes="""Now here's the first problem. This API is C++ only. Virtual methods, templates, unique_ptr, std::string. And CGO does not speak C++. CGO can only call plain C functions. DuckDB does ship a C API, the duckdb.h header that the Go bindings are built on, but the virtual file system is not part of it. There is no C API for file systems.

So the bridge has to be a C++ class. We implement a subclass of duckdb::FileSystem, called GoFileSystem, and its only job is to translate every virtual method call into a plain C function call, because plain C functions are exactly the thing that Go can provide.""",
    ),
    dict(
        kind="code",
        title="The C functions we wish existed",
        lang="cpp",
        code="""
extern "C" {
	int     duckfs_file_open(int id, const char *path);
	int64_t duckfs_file_size(int id);
	int64_t duckfs_file_read_at(int id, void *buf,
	                            int64_t size, int64_t off);
	int     duckfs_file_close(int id);
	char   *duckfs_glob(int id, const char *pattern);
	// ...
}

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
""",
        size=12,
        notes="""On the C++ side, we declare the C functions we wish existed.

And each method of GoFileSystem is a one-liner that forwards to one of them, plus error translation, because DuckDB reports errors with C++ exceptions and our C functions report them with negative return values.""",
    ),
    dict(
        kind="code",
        title="//export: C calls Go",
        lang="go",
        code="""
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
""",
        size=13,
        notes="""Where do those C functions come from? This is my favorite part of CGO, and it's the part people use the least: it goes both ways. Everyone knows Go can call C. But with the //export directive, C can call Go. You write a Go function, you put //export and its name in a comment above it, and the Go toolchain generates a C symbol for it that any C or C++ code in the binary can call.

Here's the Go side of the read operation we just saw.

Look at what happens here: DuckDB hands us a pointer to its own buffer, and unsafe.Slice wraps it as a Go byte slice, no copy. We call ReadAt on the fs.File and the data lands directly in DuckDB's memory. The whole crossing costs one function call and zero allocations.""",
    ),
    dict(
        kind="code",
        title="Registration",
        lang="cpp",
        code="""
duckdb_state duckfs_register_subsystem(duckdb_database database, int id) {
	auto wrapper = reinterpret_cast<duckdb::DatabaseWrapper *>(database);
	auto &fs = duckdb::FileSystem::GetFileSystem(
		*wrapper->database->instance.get());
	fs.RegisterSubSystem(duckdb::make_uniq<duckdb::GoFileSystem>(id));
	return DuckDBSuccess;
}
""",
        size=14,
        notes="""There's one more piece of plumbing: registration. When you create a connector, we need to tell the DuckDB instance "here is a new file system subsystem". The C API gives us an opaque duckdb_database handle, and our extension casts it back to the internal C++ wrapper to reach the FileSystem registry.

Is this a little bold? Yes. But that's a decision you get to make when you own the glue layer: we pin the DuckDB version in our build anyway, so it's a controlled risk, checked by tests.""",
    ),
    dict(
        kind="code",
        title="No Go pointer ever crosses the line",
        lang="go",
        code="""
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
""",
        size=14,
        notes="""Now, you may have noticed: there is not a single Go pointer crossing into C++ in any of this code. Everything is done with these little integer IDs. That's not an accident, and it's the second implementation challenge, because anyone who bridges Go with C will hit it.

The natural design would be: open a file, hand C++ a pointer to the fs.File, and have every read pass that pointer back. But the CGO pointer passing rules say no. C memory must not hold Go pointers across calls: the garbage collector can't see into C++, so nothing would keep the object alive, or stop it from being moved.

So instead of passing pointers out, we keep every Go object at home, in a registry, and we hand C++ a claim ticket.

Two registries: one for mounted file systems, one for open files. When DuckDB opens a file, we register the fs.File and return its index. Every subsequent operation carries that integer, and the trampoline looks the object up again. When the file closes, we unregister it, and the object becomes garbage like any other Go value: the lifetime of the Go object is explicitly tied to the lifetime of DuckDB's file handle. And the mutex matters, because DuckDB calls us from its own worker threads, not from a goroutine.

And that's really the whole bridge: a C++ class that turns virtual calls into C calls, exported Go functions that turn C calls into interface calls, and an ID registry so no pointer ever crosses the line. Under a thousand lines, total.""",
    ),
    dict(
        kind="section",
        title="Part 3 — Propagating context.Context",
        notes="""So at this point we have a working bridge, and if all you need is to query local, static data, you're done. But the moment we put this in production, we hit a usability problem that I think is the most instructive part of the whole project: context.

An RPC comes in. It carries a context.Context, and that context carries everything: the deadline, the cancellation signal, the tenant identity, the OpenTelemetry span. Every I/O operation we perform on behalf of that request is supposed to flow through that context. That's the contract of a well-behaved Go service.""",
    ),
    dict(
        kind="diagram",
        title="The context is gone",
        diagram=(
            "request ctx enters the handler goroutine, crosses into C++ where "
            "DuckDB fans out to worker threads, and re-enters Go via the "
            "bridge on a different thread with no ctx; a dotted line shows "
            "the path the context needs to travel. Overlay: "
            "func (fsys *fileSystem) Open(name string) (fs.File, error)"
        ),
        notes="""Now trace the path of a read. The request handler executes a SQL query. The query descends into DuckDB, into C++. DuckDB schedules work on its own worker threads, and somewhere down there, a Parquet reader asks for bytes, and the call comes back up into our Go code through the bridge. And what do we receive?

A string. fs.FS knows nothing about context, the interface is deliberately minimal. And there's no goroutine-local magic to save us either: this call isn't even coming from the goroutine that ran the query, it's coming from a DuckDB worker thread. The context is gone.

So how do we get the request's context back on the other side of a C++ thread pool?""",
    ),
    dict(
        kind="code",
        title="The file system is a value — values capture",
        lang="go",
        code="""
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
""",
        size=13,
        notes="""With a pattern you've already seen once in this talk: the file system is just a value, and values can capture things. When the request arrives, we construct the fs.FS for that specific request, and we store the context inside it.

Open re-injects the captured context into everything it does, and the file it returns carries it too, so every ReadAt becomes an object store request made with the request's context. Deadline, cancellation, tracing span: they all made it across the C++ thread pool, smuggled inside the file system value itself.

Now, I know what some of you are thinking, because it's written in the context package documentation: "do not store a context inside a struct type". As a general rule, that's right. But the rule exists because a context stored in a long-lived object outlives its request. Here, the file system value IS the request-scoped object: it's created when the query starts, and it dies with the query. When the lifetimes coincide, capturing the context is correct — this is the escape hatch the guideline leaves open, and crossing a foreign thread pool is precisely what it's for.""",
    ),
    dict(
        kind="code",
        title="Pooled instances, per-request context",
        lang="go",
        code="""
type duckDBFileSystem struct{ fsys fs.FS }

func (d *duckDBFileSystem) Open(name string) (fs.File, error) {
	if d.fsys == nil {
		return nil, fs.ErrNotExist
	}
	return d.fsys.Open(name)
}

func (d *duckDBFileSystem) Reset(fsys fs.FS) { d.fsys = fsys }

func (p *Pool) Query(ctx context.Context, registry storage.Registry,
	sql string, args ...any) (array.RecordReader, error) {

	db := p.get() // pooled instance, created with duckfs.Open(...)

	fsys := storage.FS(ctx, registry) // capture this request's context
	db.fileSystem.Reset(fsys)         // mount it for this query

	// ... run the query, return the instance to the pool when done
}
""",
        size=12,
        notes="""One last wrinkle, from performance. Creating a DuckDB connector is expensive, so we pool instances and reuse them. But the file system is registered with DuckDB once, at creation. How do we swap in a per-request file system on a pooled instance? One more layer of indirection: the file system we actually mount is a tiny resettable wrapper, and each query points it at the current request's context-bound file system.

When the query finishes, we reset the wrapper to nil and put the instance back in the pool. The context never leaks past its request, and the pooled DuckDB instance never holds onto anything request-scoped between queries.""",
    ),
    dict(
        kind="diagram",
        title="One trace, end to end",
        diagram=(
            "screenshot-style trace waterfall — RPC span at top, query span "
            "below, dozens of object store GET spans underneath with varying "
            "durations, one highlighted showing an authentication error"
        ),
        notes="""And this is what the payoff looks like: one trace, end to end. The incoming RPC at the top, the SQL query below it, and then every single object store read that DuckDB triggered, each with its timing, each with its result, hanging off the request's span. When a query is slow, we don't guess anymore. We look.""",
    ),
    dict(
        kind="bullets",
        title="Takeaways",
        bullets=[
            "Reuse great software; invest in the glue layer",
            "  DuckDB's VFS + Go's fs.FS met in the middle — SQLite has a hook too",
            "The techniques travel: C++ shim, //export, integer handles,",
            "  request-scoped values to carry context across thread pools",
            "CGO: know the problems you sign up for — then design them away",
        ],
        notes="""So let me leave you with three takeaways.

First, on software design. In the age of LLMs, the bar for what should be rewritten versus reused has moved, no question. But there are still high-quality pieces of software out there that we should reuse, and when we do, the glue layer is where the leverage is. DuckDB exposing a virtual file system abstraction, and Go shipping fs.FS in the standard library, is what made a one-thousand-line bridge possible. That's not luck, that's two well-designed systems meeting in the middle. And the pattern generalizes: most serious C libraries that do I/O expose some virtual file system hook. SQLite has one. If you can connect that hook to io/fs, everything I showed you today applies.

Second, the implementation techniques are the reusable part: a thin C++ class to translate an object-oriented API into plain C functions, //export to let C call Go, integer handles instead of pointers so the garbage collector stays free, and request-scoped values to carry context across a foreign thread pool. That toolbox works for far more than DuckDB.

And third, I hope you walk away with a more refined sense of when CGO is the right tool. Not "never", not "whatever": know the problems you're signing up for, and know that with the right abstraction at the boundary, you can make most of them disappear.""",
    ),
    dict(
        kind="section",
        title="github.com/firetiger-oss/go-duckfs",
        notes="""Everything I showed today is open-source at github.com/firetiger-oss/go-duckfs. It's MIT licensed, issues and contributions are very welcome, there's plenty left to build. And as always, remember to support your open-source maintainers by being generous with GitHub stars.

Thank you GopherCon! I think we have a couple of minutes for questions.""",
    ),
]


def build(path):
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    for s in SLIDES:
        slide = prs.slides.add_slide(blank)
        kind = s["kind"]

        if kind == "title":
            box = textbox(slide, 900000, 2300000, 10400000, 1400000)
            p = box.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = s["title"]
            r.font.name = BODY_FONT
            r.font.size = Pt(44)
            r.font.bold = True
            r.font.color.rgb = INK
            sub = textbox(slide, 900000, 3900000, 10400000, 1200000)
            for i, line in enumerate(s["subtitle"].split("\n")):
                p = sub.text_frame.paragraphs[0] if i == 0 else sub.text_frame.add_paragraph()
                p.alignment = PP_ALIGN.CENTER
                r = p.add_run()
                r.text = line
                r.font.name = BODY_FONT
                r.font.size = Pt(20)
                r.font.color.rgb = MUTED

        elif kind == "section":
            box = textbox(slide, 900000, 2800000, 10400000, 1200000)
            p = box.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = s["title"]
            r.font.name = BODY_FONT
            r.font.size = Pt(36)
            r.font.bold = True
            r.font.color.rgb = ACCENT

        elif kind == "statement":
            add_statement(slide, s["text"])

        elif kind == "bullets":
            add_title(slide, s["title"])
            add_bullets(slide, s["bullets"])

        elif kind == "code":
            add_title(slide, s["title"])
            add_code(slide, s["code"], size=s.get("size", 14))

        elif kind == "diagram":
            add_title(slide, s["title"])
            add_diagram_placeholder(slide, s["diagram"])

        set_notes(slide, s["notes"])

    prs.save(path)
    print(f"wrote {path}: {len(prs.slides.slides if hasattr(prs.slides, 'slides') else prs.slides._sldIdLst)} slides")


if __name__ == "__main__":
    build("slides.pptx")
