#!/usr/bin/env node
import process from 'node:process';
import concatStream from 'concat-stream';
import remarkGemoji from 'remark-gemoji';
import remarkParse from 'remark-parse';
import remarkStringify from 'remark-stringify';
import { read } from 'to-vfile';
import { unified } from 'unified';

process.stdin.pipe(
    concatStream(function (buf) {
        const output = unified()
            .use(remarkParse)
            .use(remarkGemoji)
            .use(remarkStringify)
            .processSync(buf);    
        process.stdout.write(String(output));
    })
)
