// Grammar: python
// Generated from: tests/fixtures/python/node-types.json
// Generated from: tests/fixtures/python/queries/highlights.scm
// Generated from: tests/fixtures/python/queries/tags.scm

package python

#NodeType: {
    type: string
    named: bool
    fields?: _
    children?: _
    subtypes?: [..._]
}

#expression_statement: #NodeType & {
    type: "expression_statement"
    named: true
}

#identifier: #NodeType & {
    type: "identifier"
    named: true
}

#module: #NodeType & {
    type: "module"
    named: true
}
