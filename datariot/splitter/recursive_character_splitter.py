import copy
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Iterable

from datariot.__spi__.splitter import Splitter, Chunk


@dataclass
class RecursiveCharacterSplitter(Splitter):
    """
Splitting text by recursively look at characters.

Recursively tries to split by different characters to find one
that works.

Args:
    chunk_size: Maximum size of chunks to return
    chunk_overlap: Overlap in characters between chunks
    separators: The separators to use for text splitting
    keep_separator: Whether to keep the separator in the chunks
    is_separator_regex: Indicates if the separator is a regex
    strip_whitespace: If `True`, strips whitespace from the start and end of
                          every document
"""

    chunk_size: int = 4000
    chunk_overlap: int = 200
    separators: List[str] = field(default_factory=lambda: ["\n\n", "\n", " ", ""])
    keep_separator: bool = True
    is_separator_regex: bool = False
    strip_whitespace: bool = True

    def _split_text(self, text: str, separators: List[str]) -> List[Chunk]:
        """Split incoming text and return chunks."""
        final_chunks = []
        # Get appropriate separator to use
        separator = separators[-1]
        new_separators = []
        for i, _s in enumerate(separators):
            _separator = _s if self.is_separator_regex else re.escape(_s)
            if _s == "":
                separator = _s
                break
            if re.search(_separator, text):
                separator = _s
                new_separators = separators[i + 1:]
                break

        _separator = separator if self.is_separator_regex else re.escape(separator)
        splits = self.split_text_with_regex(text, _separator)

        # Now go merging things, recursively splitting longer texts.
        _good_splits = []
        _separator = "" if self.keep_separator else separator
        for s in splits:
            if len(s) < self.chunk_size:
                _good_splits.append(s)
            else:
                if _good_splits:
                    merged_text = self.merge_splits(_good_splits, _separator)
                    final_chunks.extend([Chunk(e) for e in merged_text])
                    _good_splits = []
                if not new_separators:
                    final_chunks.append(Chunk(s))
                else:
                    other_info = self._split_text(s, new_separators)
                    final_chunks.extend(other_info)
        if _good_splits:
            merged_text = self.merge_splits(_good_splits, _separator)
            final_chunks.extend(merged_text)
        return final_chunks

    def create_documents(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> List[Chunk]:
        """Create documents from a list of texts."""
        _metadatas = metadatas or [{}] * len(texts)
        documents = []
        for i, text in enumerate(texts):
            for chunk in self._split_text(text, separators=self.separators):
                metadata = copy.deepcopy(_metadatas[i])
                new_doc = Chunk(text=chunk, data=metadata)
                documents.append(new_doc)
        return documents

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text, self._separators)

    def split_documents(self, documents: Iterable[Chunk]) -> List[Chunk]:
        """Split documents."""
        texts, metadatas = [], []
        for doc in documents:
            texts.append(doc.text)
            metadatas.append(doc.data)
        return self.create_documents(texts, metadatas=metadatas)

    def __call__(self, text: str) -> List[Chunk]:
        return self._split_text(text, self.separators)

    def split_text_with_regex(self, text: str, separator: str) -> List[str]:
        # Now that we have the separator, split the text
        if separator:
            if self.keep_separator:
                # The parentheses in the pattern keep the delimiters in the result.
                _splits = re.split(f"({separator})", text)
                splits = [_splits[i] + _splits[i + 1] for i in range(1, len(_splits), 2)]
                if len(_splits) % 2 == 0:
                    splits += _splits[-1:]
                splits = [_splits[0]] + splits
            else:
                splits = re.split(separator, text)
        else:
            splits = list(text)
        return [s for s in splits if s != ""]

    def merge_splits(self, splits: Iterable[str], separator: str) -> List[str]:
        # We now want to combine these smaller pieces into medium size
        # chunks to send to the LLM.
        separator_len = len(separator)

        docs = []
        current_doc: List[str] = []
        total = 0
        for d in splits:
            _len = len(d)
            if (total + _len + (separator_len if len(current_doc) > 0 else 0) > self.chunk_size):
                if total > self.chunk_size:
                    logging.warning(
                        f"Created a chunk of size {total}, "
                        f"which is longer than the specified {self.chunk_size}"
                    )
                if len(current_doc) > 0:
                    doc = self.join_docs(current_doc, separator)
                    if doc is not None:
                        docs.append(doc)
                    # Keep on popping if:
                    # - we have a larger chunk than in the chunk overlap
                    # - or if we still have any chunks and the length is long
                    while total > self.chunk_overlap or (
                            total + _len + (separator_len if len(current_doc) > 0 else 0)
                            > self.chunk_size
                            and total > 0
                    ):
                        total -= len(current_doc[0]) + (
                            separator_len if len(current_doc) > 1 else 0
                        )
                        current_doc = current_doc[1:]
            current_doc.append(d)
            total += _len + (separator_len if len(current_doc) > 1 else 0)
        doc = self.join_docs(current_doc, separator)
        if doc is not None:
            docs.append(doc)
        return docs

    def join_docs(self, docs: List[str], separator: str) -> Optional[str]:
        text = separator.join(docs)
        if self.strip_whitespace:
            text = text.strip()
        if text == "":
            return None
        else:
            return text
