"""pygls-backed Yuho language server."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from yuho import __version__
from yuho.parser import get_parser
from yuho.parser.wrapper import ParseResult, Parser


@dataclass(frozen=True)
class ParsedDocument:
    uri: str
    file: str
    source: str
    result: ParseResult


class YuhoLanguageServer(LanguageServer):
    def __init__(self, parser: Optional[Parser] = None) -> None:
        super().__init__("yuho-lsp", __version__)
        self.parser = parser or get_parser()
        self.parsed_documents: dict[str, ParsedDocument] = {}

    def parse_source(self, uri: str, source: str) -> ParsedDocument:
        file = uri_to_file(uri)
        result = self.parser.parse(source, file=file)
        parsed = ParsedDocument(uri=uri, file=file, source=source, result=result)
        self.parsed_documents[uri] = parsed
        return parsed

    def parse_text_document(self, uri: str) -> Optional[ParsedDocument]:
        document = self.workspace.get_text_document(uri)
        if document is None:
            return None
        return self.parse_source(uri, document.source)

    def cached_parse(self, uri: str) -> Optional[ParsedDocument]:
        return self.parsed_documents.get(uri)

    def drop_document(self, uri: str) -> None:
        self.parsed_documents.pop(uri, None)


def create_server() -> YuhoLanguageServer:
    server = YuhoLanguageServer()
    register_features(server)
    return server


def register_features(server: YuhoLanguageServer) -> None:
    @server.feature(types.TEXT_DOCUMENT_DID_OPEN)
    def did_open(params: types.DidOpenTextDocumentParams) -> None:
        server.parse_source(params.text_document.uri, params.text_document.text)

    @server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
    def did_change(params: types.DidChangeTextDocumentParams) -> None:
        document = server.workspace.get_text_document(params.text_document.uri)
        if document is not None:
            server.parse_source(params.text_document.uri, document.source)

    @server.feature(types.TEXT_DOCUMENT_DID_SAVE)
    def did_save(params: types.DidSaveTextDocumentParams) -> None:
        server.parse_text_document(params.text_document.uri)

    @server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
    def did_close(params: types.DidCloseTextDocumentParams) -> None:
        server.drop_document(params.text_document.uri)


def uri_to_file(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return uri
    path = unquote(parsed.path)
    if parsed.netloc:
        path = f"//{parsed.netloc}{path}"
    return str(Path(path))


def main() -> None:
    create_server().start_io()


if __name__ == "__main__":
    main()
