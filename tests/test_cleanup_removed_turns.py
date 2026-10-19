"""
`session-memory cleanup --turn N` must survive later captures.

The session-end hook fires per turn (both Claude Code and agy wire it to
their Stop event) and `SessionIndex` derives "already indexed" purely from
the persisted chunk list, so a removed trailing turn is indistinguishable
from a never-indexed one and used to be re-added by the very next capture.
These tests pin the documented no-resurrection guarantee of `remove_turns`.

Embeddings are stubbed: the suite runs model-free (no sentence-transformers
download), FAISS/BM25 themselves are real.
"""

import numpy as np
import pytest

from session_memory.capture.transcript_reader import Turn
from session_memory.indexing import session_index as session_index_module
from session_memory.indexing.embedder import EMBEDDING_DIM
from session_memory.indexing.session_index import SessionIndex
from session_memory.store import cleanup as cleanup_module
from session_memory.store.cleanup import remove_turns
from session_memory.store.removed_turns import RemovedTurns

SESSION_ID = "sess-abc-123"
COMMIT_HASH = "deadbeef"


def _fake_embed_texts(texts):
    vectors = np.zeros((len(texts), EMBEDDING_DIM), dtype="float32")
    for position, text in enumerate(texts):
        vectors[position, sum(text.encode("utf-8")) % EMBEDDING_DIM] = 1.0
    return vectors


@pytest.fixture(autouse=True)
def _stub_embedder(monkeypatch):
    monkeypatch.setattr(session_index_module, "embed_texts", _fake_embed_texts)
    monkeypatch.setattr(cleanup_module, "embed_texts", _fake_embed_texts)


def _turns(count, start=0):
    return [
        Turn(
            developer_text=f"question {index}",
            assistant_text=f"answer {index}",
            timestamp=1_700_000_000 + index,
            commit_hash=COMMIT_HASH,
            session_id=SESSION_ID,
            turn_index=index,
        )
        for index in range(start, start + count)
    ]


def _indexed_turn_indices(memory_dir):
    index = SessionIndex(memory_dir, COMMIT_HASH, SESSION_ID)
    return sorted(chunk.turn_index for chunk in index.chunks)


def test_removing_trailing_turn_stays_removed_on_next_capture(tmp_path):
    memory_dir = str(tmp_path)
    turns = _turns(3)
    SessionIndex(memory_dir, COMMIT_HASH, SESSION_ID).add_turns(turns)
    assert _indexed_turn_indices(memory_dir) == [0, 1, 2]

    assert remove_turns(memory_dir, SESSION_ID, [2]) == 1
    assert _indexed_turn_indices(memory_dir) == [0, 1]

    # The next Stop hook re-parses the same transcript and hands the full
    # turn list back: nothing may be re-added.
    new_chunks = SessionIndex(memory_dir, COMMIT_HASH, SESSION_ID).add_turns(turns)
    assert new_chunks == []
    assert _indexed_turn_indices(memory_dir) == [0, 1]


def test_removing_all_turns_stays_removed_on_next_capture(tmp_path):
    memory_dir = str(tmp_path)
    turns = _turns(3)
    SessionIndex(memory_dir, COMMIT_HASH, SESSION_ID).add_turns(turns)

    assert remove_turns(memory_dir, SESSION_ID, [0, 1, 2]) == 3
    assert _indexed_turn_indices(memory_dir) == []

    new_chunks = SessionIndex(memory_dir, COMMIT_HASH, SESSION_ID).add_turns(turns)
    assert new_chunks == []
    assert _indexed_turn_indices(memory_dir) == []


def test_removed_trailing_turn_stays_removed_when_session_grows(tmp_path):
    memory_dir = str(tmp_path)
    SessionIndex(memory_dir, COMMIT_HASH, SESSION_ID).add_turns(_turns(3))
    assert remove_turns(memory_dir, SESSION_ID, [1, 2]) == 2

    new_chunks = SessionIndex(memory_dir, COMMIT_HASH, SESSION_ID).add_turns(_turns(4))
    assert sorted(chunk.turn_index for chunk in new_chunks) == [3]
    assert _indexed_turn_indices(memory_dir) == [0, 3]


def test_absent_turn_index_is_not_recorded_as_removed(tmp_path):
    memory_dir = str(tmp_path)
    SessionIndex(memory_dir, COMMIT_HASH, SESSION_ID).add_turns(_turns(2))

    # Turn 5 doesn't exist yet: requesting it must not suppress a real
    # turn 5 captured later.
    assert remove_turns(memory_dir, SESSION_ID, [5]) == 0
    assert RemovedTurns(memory_dir).removed(SESSION_ID) == set()

    new_chunks = SessionIndex(memory_dir, COMMIT_HASH, SESSION_ID).add_turns(_turns(6))
    assert sorted(chunk.turn_index for chunk in new_chunks) == [2, 3, 4, 5]
    assert _indexed_turn_indices(memory_dir) == [0, 1, 2, 3, 4, 5]


def test_removed_turns_persist_across_processes(tmp_path):
    memory_dir = str(tmp_path)
    RemovedTurns(memory_dir).record_removed(SESSION_ID, [4, 2])
    RemovedTurns(memory_dir).record_removed(SESSION_ID, [4])

    reloaded = RemovedTurns(memory_dir)
    assert reloaded.removed(SESSION_ID) == {2, 4}
    assert reloaded.removed("other-session") == set()
