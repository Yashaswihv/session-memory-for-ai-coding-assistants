import os
import pickle
import re
from collections import Counter
from typing import List, Tuple

import click

from session_memory.indexing.bm25_index import Bm25Index
from session_memory.indexing.chunker import Chunk
from session_memory.indexing.embedder import embed_texts
from session_memory.indexing.faiss_index import FaissIndex
from session_memory.redaction.patterns import RedactionPattern
from session_memory.redaction.reporter import format_report, merge_counts
from session_memory.redaction.sanitizer import sanitize_text
from session_memory.retrieval.searcher import find_raw_session_bases
from session_memory.store.workspace import resolve_workspace


def _parse_extra_pattern(spec: str) -> RedactionPattern:
    label, _, pattern = spec.partition("=")
    if not pattern:
        raise click.BadParameter(f"expected LABEL=REGEX, got {spec!r}")
    return RedactionPattern.from_regex(label.strip(), re.compile(pattern))


def _sanitize_session(base: str, extra_patterns: List[RedactionPattern]) -> Counter:
    counts_list: List[Counter] = []

    md_path = base + ".md"
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            raw_md = f.read()
        sanitized_md, md_counts = sanitize_text(raw_md, extra_patterns)
        with open(base + ".sanitized.md", "w", encoding="utf-8") as f:
            f.write(sanitized_md)
        counts_list.append(md_counts)

    chunks_path = base + ".chunks.pkl"
    if not os.path.exists(chunks_path):
        return merge_counts(counts_list)

    with open(chunks_path, "rb") as f:
        chunks: List[Chunk] = pickle.load(f)

    sanitized_chunks: List[Chunk] = []
    for chunk in chunks:
        sanitized_text_value, chunk_counts = sanitize_text(chunk.text, extra_patterns)
        counts_list.append(chunk_counts)
        sanitized_chunks.append(
            Chunk(
                text=sanitized_text_value,
                session_id=chunk.session_id,
                turn_index=chunk.turn_index,
                chunk_index=chunk.chunk_index,
                timestamp=chunk.timestamp,
                commit_hash=chunk.commit_hash,
            )
        )

    with open(base + ".sanitized.chunks.pkl", "wb") as f:
        pickle.dump(sanitized_chunks, f)

    faiss_index = FaissIndex.create_empty(base + ".sanitized.faiss")
    faiss_index.add(embed_texts([c.text for c in sanitized_chunks]))
    faiss_index.save()

    bm25_index = Bm25Index.build([c.text for c in sanitized_chunks])
    bm25_index.save(base + ".sanitized.bm25.pkl")

    return merge_counts(counts_list)


@click.command(name="sanitize")
@click.option("--path", default=".", show_default=True, help="Workspace directory to sanitize.")
@click.option(
    "--pattern",
    "extra_pattern_specs",
    multiple=True,
    help="Extra redaction pattern as LABEL=REGEX (repeatable).",
)
def cmd_sanitize(path: str, extra_pattern_specs: Tuple[str, ...]):
    """
    Reads raw conversation logs, applies redaction patterns, and writes a
    parallel *.sanitized.* file set (log + rebuilt FAISS/BM25/chunks)
    alongside the raw files — the recommended unit for sharing. Raw files
    are untouched and remain gitignored; only the *.sanitized.* files are
    meant to be added to version control (paper section 3.3).
    """
    root = os.path.realpath(path)
    workspace = resolve_workspace(root)
    if workspace is None:
        click.echo("No .conversation-memory/ reachable from this directory.")
        return

    extra_patterns = [_parse_extra_pattern(spec) for spec in extra_pattern_specs]
    bases = find_raw_session_bases(workspace.memory_dir)
    if not bases:
        click.echo("No raw session logs found to sanitize.")
        return

    all_counts = [_sanitize_session(base, extra_patterns) for base in bases]

    click.echo(format_report(merge_counts(all_counts), len(bases)))
    click.echo(f"Sanitized {len(bases)} session file(s). Review the *.sanitized.* files before sharing.")
