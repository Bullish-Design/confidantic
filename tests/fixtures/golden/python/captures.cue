// Grammar: python
// Generated from: tests/fixtures/python/queries/highlights.scm
// Generated from: tests/fixtures/python/queries/tags.scm

package python

#Capture: {
    name: string
    query_type: string
    pattern?: string
    source_file: string
    source_line?: int
}

#captures: {
    "highlights": {
        "@function.definition": [
            #Capture & {
                name: "@function.definition"
                query_type: "highlights"
                source_file: "tests/fixtures/python/queries/highlights.scm"
                source_line: 3
            },
        ]
        "@type.definition": [
            #Capture & {
                name: "@type.definition"
                query_type: "highlights"
                source_file: "tests/fixtures/python/queries/highlights.scm"
                source_line: 6
            },
        ]
        "@variable": [
            #Capture & {
                name: "@variable"
                query_type: "highlights"
                source_file: "tests/fixtures/python/queries/highlights.scm"
                source_line: 8
            },
        ]
    }
    "tags": {
        "@definition.class": [
            #Capture & {
                name: "@definition.class"
                query_type: "tags"
                source_file: "tests/fixtures/python/queries/tags.scm"
                source_line: 6
            },
        ]
        "@definition.function": [
            #Capture & {
                name: "@definition.function"
                query_type: "tags"
                source_file: "tests/fixtures/python/queries/tags.scm"
                source_line: 3
            },
        ]
    }
}
