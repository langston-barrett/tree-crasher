# tree-crasher

tree-crasher is an easy-to-use grammar-based black-box fuzzer. It parses a
number of input files using [tree-sitter][tree-sitter] grammars, and produces
new files formed by splicing together their ASTs.

tree-crasher aims to occupy a different niche from more advanced grammar-based 
fuzzers like Gramatron, Nautilus, and Grammarinator. Rather than achieve
maximal coverage and bug-finding through complete, hand-written grammars and
complex techniques like coverage-based feedback, tree-crasher aims to achieve
maximal ease-of-use by using off-the-shelf tree-sitter grammars and not
requiring any instrumentation (nor even source code) for the target. In short,
tree-crasher wants to be the [Radamsa][radamsa] of grammar-based fuzzing.

tree-sitter grammars are resistant to syntax errors. Therefore, tree-crasher
can even mutate syntactically-invalid inputs! You can also use tree-crasher
with an incomplete grammar.

tree-crasher uses [treereduce][treereduce] to automatically minimize generated
test-cases.

## Examples

See the [usage docs](usage.md).

## Bugs found

tree-crasher uses [tree-splicer][tree-splicer] to generate test cases, see the
list of bugs found in that project's README.

If you find a bug with tree-crasher, please let me know! One great way to do so
would be to submit a PR to tree-splicer to add it to the README.

## Supported languages

tree-crasher currently ships pre-built executables for the following languages:

- [C](./crates/tree-crasher-c)
- [CSS](./crates/tree-crasher-css)
- [JavaScript](./crates/tree-crasher-javascript)
- [Regex](./crates/tree-crasher-regex)
- [Rust](./crates/tree-crasher-rust)
- [SQL](./crates/tree-crasher-sql)
- [TypeScript](./crates/tree-crasher-typescript)

Additionally, the following fuzzers can be built from source or installed via
crates.io:

- [HTML](./crates/tree-crasher-html)
- [Ruby](./crates/tree-crasher-ruby)

Languages are very easy to add, so file an issue or a PR if you want a new one!

## How it works

tree-crasher is mostly a thin wrapper around [tree-splicer][tree-splicer] that
runs it in parallel. When "interesting" test cases are found, they're handed
off to [treereduce][treereduce].

[radamsa]: https://gitlab.com/akihe/radamsa
[tree-sitter]: https://tree-sitter.github.io/tree-sitter/
[tree-splicer]: https://github.com/langston-barrett/tree-splicer
[treereduce]: https://github.com/langston-barrett/treereduce