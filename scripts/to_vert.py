#!/usr/bin/env python3
"""Convert HPLT v3 JSONL to manatee vertical format.

HPLT v3 JSONL structure (one line = one shard file):
  {"filename": "...", "documents": [{doc}, ...]}

Each document has abbreviated fields:
  id    - document ID
  lang  - list of detected language tags (primary = first)
  u     - source URL
  text  - document text (newline-delimited paragraphs)

Output vertical format:
  <doc id="..." lang="..." url="...">
  <s>
  token
  ...
  </s>
  </doc>

Positional attribute: word (single column, one token per line).
Sentence boundaries: each non-empty text line = one <s>.
Tokenization: whitespace split.
"""

import argparse
import json
import sys
import xml.sax.saxutils as saxutils


def escape(value):
    return saxutils.escape(str(value))


def iter_docs(input_path, limit):
    """Yield individual documents across all shard lines up to limit."""
    count = 0
    with open(input_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: skipping malformed line ({e})", file=sys.stderr)
                continue
            for doc in record.get("documents", []):
                if limit is not None and count >= limit:
                    return
                yield doc
                count += 1


def to_vert(input_path, output_path, limit):
    count = 0
    skipped = 0
    with open(output_path, "w", encoding="utf-8") as out:
        for doc in iter_docs(input_path, limit):
            text = doc.get("text", "").strip()
            if not text:
                skipped += 1
                continue

            lang_list = doc.get("lang", [])
            lang = escape(lang_list[0] if lang_list else "")
            doc_id = escape(doc.get("id", ""))
            url = escape(doc.get("u", ""))

            out.write(f'<doc id="{doc_id}" lang="{lang}" url="{url}">\n')
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                tokens = line.split()
                if not tokens:
                    continue
                out.write("<s>\n")
                for token in tokens:
                    out.write(token + "\n")
                out.write("</s>\n")
            out.write("</doc>\n")
            count += 1

    print(f"Wrote {count} documents, skipped {skipped} empty.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Convert HPLT v3 JSONL to manatee vertical format."
    )
    parser.add_argument("--input", required=True, help="Input HPLT v3 JSONL file")
    parser.add_argument("--output", required=True, help="Output .vert file")
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Max documents to convert (0 = all, default: 1000)",
    )
    args = parser.parse_args()
    limit = args.limit if args.limit > 0 else None
    to_vert(args.input, args.output, limit)


if __name__ == "__main__":
    main()
