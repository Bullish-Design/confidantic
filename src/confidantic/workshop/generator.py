"""Deterministic CUE generation for Tree-sitter workshop inputs."""

from __future__ import annotations

from datetime import timezone
from hashlib import sha1
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .models import WorkshopInput


class CueGenerator:
    """Generate deterministic CUE files from a ``WorkshopInput`` instance."""

    def __init__(self, workshop_input: WorkshopInput):
        self.input = workshop_input
        self.grammar = workshop_input.grammar_name

    def generate(self, output_dir: Path) -> list[Path]:
        """Generate all phase-2 CUE schema files in deterministic order."""
        output_dir = Path(output_dir)
        self._validate_output_dir(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_paths = self._get_output_paths(output_dir)
        contents = {
            "captures": self._generate_captures(),
            "metadata": self._generate_metadata(),
            "node_types": self._generate_node_types(),
        }

        for key, path in output_paths.items():
            self._write_atomic(path, contents[key])

        return [output_paths[name] for name in sorted(output_paths)]

    def _validate_output_dir(self, output_dir: Path) -> None:
        normalized_parts = tuple(part.lower() for part in output_dir.parts)
        if len(normalized_parts) < 3 or "build" not in normalized_parts:
            raise ValueError(f"Output directory must be inside build/: {output_dir}")

    def _get_output_paths(self, output_dir: Path) -> dict[str, Path]:
        return {
            "captures": output_dir / "captures.cue",
            "metadata": output_dir / "metadata.cue",
            "node_types": output_dir / "node_types.cue",
        }

    def _generate_provenance_comments(self, source_paths: list[str]) -> list[str]:
        lines = [f"// Grammar: {self.grammar}"]
        for source in source_paths:
            lines.append(f"// Generated from: {source}")
        return lines

    def _generate_node_types(self) -> str:
        source_paths = sorted(
            [
                str(path)
                for key, path in self.input.source_paths.items()
                if key == "node_types" or key.startswith("query.")
            ]
        )
        lines: list[str] = self._generate_provenance_comments(source_paths)
        lines.extend(["", f"package {self.grammar}", "", "#NodeType: {", "    type: string", "    named: bool", "    fields?: _", "    children?: _", "    subtypes?: [..._]", "}"])

        used_labels: set[str] = set()
        for node in sorted(self.input.node_types.nodes, key=lambda item: item.type):
            label = self._definition_label(node.type, used_labels)
            lines.extend([
                "",
                f"{label}: #NodeType & {{",
                f"    type: {self._cue_value(node.type)}",
                f"    named: {self._cue_value(node.named)}",
            ])
            if node.fields:
                lines.append(f"    fields: {self._cue_value(node.fields, indent=4)}")
            if node.children is not None:
                lines.append(f"    children: {self._cue_value(node.children, indent=4)}")
            if node.subtypes:
                lines.append(f"    subtypes: {self._cue_value(node.subtypes, indent=4)}")
            lines.append("}")

        return "\n".join(lines) + "\n"

    def _generate_captures(self) -> str:
        source_paths = sorted(str(query.file_path) for query in self.input.query_files)
        lines: list[str] = self._generate_provenance_comments(source_paths)
        lines.extend(["", f"package {self.grammar}", "", "#Capture: {", "    name: string", "    query_type: string", "    pattern?: string", "    source_file: string", "    source_line?: int", "}", "", "#captures: {"])

        grouped = sorted(self.input.query_files, key=lambda item: (item.query_type, str(item.file_path)))
        for query in grouped:
            lines.append(f"    {self._cue_value(query.query_type)}: {{")
            capture_map: dict[str, list[Any]] = {}
            for capture in sorted(query.captures, key=lambda item: (item.name, item.line or 0, item.line_number)):
                capture_map.setdefault(capture.name, []).append(capture)

            for capture_name in sorted(capture_map):
                lines.append(f"        {self._cue_value(capture_name)}: [")
                for capture in capture_map[capture_name]:
                    lines.append("            #Capture & {")
                    lines.append(f"                name: {self._cue_value(capture.name)}")
                    lines.append(f"                query_type: {self._cue_value(query.query_type)}")
                    lines.append(f"                source_file: {self._cue_value(str(query.file_path))}")
                    if capture.pattern is not None:
                        lines.append(f"                pattern: {self._cue_value(capture.pattern)}")
                    if capture.line is not None:
                        lines.append(f"                source_line: {capture.line}")
                    lines.append("            },")
                lines.append("        ]")
            lines.append("    }")
        lines.append("}")

        return "\n".join(lines) + "\n"

    def _generate_metadata(self) -> str:
        sources = sorted(
            str(path)
            for _key, path in self.input.source_paths.items()
        )
        generated_at = self.input.timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

        lines = [
            "// Grammar metadata",
            f"// Generated for grammar: {self.grammar}",
            "",
            f"package {self.grammar}",
            "",
            "#GrammarMetadata: {",
            f"    name: {self._cue_value(self.grammar)}",
            f"    generated_at: {self._cue_value(generated_at)}",
            f"    fingerprint: {self._cue_value(self.input.fingerprint())}",
            f"    confidantic_version: {self._cue_value('1.0.0a1')}",
            "    sources: [",
        ]
        for source in sources:
            lines.append(f"        {self._cue_value(source)},")
        lines.extend(["    ]", "}"])
        return "\n".join(lines) + "\n"

    def _definition_label(self, node_type: str, used_labels: set[str]) -> str:
        translated = []
        for char in node_type:
            translated.append(char if char.isalnum() else "_")
        normalized = "".join(translated).strip("_").lower() or "node"
        if normalized[0].isdigit():
            normalized = f"n_{normalized}"
        label = f"#{normalized}"
        if label in used_labels:
            digest = sha1(node_type.encode("utf-8")).hexdigest()[:8]
            label = f"{label}_{digest}"
        used_labels.add(label)
        return label

    def _cue_value(self, value: Any, *, indent: int = 0) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, list):
            if not value:
                return "[]"
            nested_indent = " " * (indent + 4)
            current_indent = " " * indent
            items = [f"{nested_indent}{self._cue_value(item, indent=indent + 4)}," for item in value]
            return "[\n" + "\n".join(items) + f"\n{current_indent}]"
        if isinstance(value, dict):
            if not value:
                return "{}"
            nested_indent = " " * (indent + 4)
            current_indent = " " * indent
            items: list[str] = []
            for key, item in sorted(value.items(), key=lambda entry: str(entry[0])):
                items.append(
                    f"{nested_indent}{self._cue_value(str(key))}: {self._cue_value(item, indent=indent + 4)}"
                )
            return "{\n" + "\n".join(items) + f"\n{current_indent}}}"
        return self._cue_value(str(value), indent=indent)

    def _write_atomic(self, target: Path, content: str) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=target.parent) as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        temp_path.replace(target)
