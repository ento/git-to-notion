import dataclasses
import datetime
import enum
import subprocess
from pathlib import Path
from typing import TypedDict, cast
from urllib.parse import urljoin

import click
from pygit2 import GIT_SORT_TIME  # pyright: ignore [reportAttributeAccessIssue]
from pygit2.repository import Repository

from .types import BuildContext, GitProvider, PathInfo


def noop(path_info: PathInfo, ctx: BuildContext, content: str) -> str:
    return content


@dataclasses.dataclass
class GitFileInfo:
    commit_sha: str
    committed_at: datetime.datetime


class PathTemplates(TypedDict):
    edit_path: str
    history_path: str
    commit_path: str


class PathTemplateContext(TypedDict):
    filepath: str
    commit: str | None


PATH_TEMPLATES_BY_PROVIDER: dict[GitProvider, PathTemplates] = {
    GitProvider.GITHUB: {
        "edit_path": "/blob/{ref}/{filepath}",
        "history_path": "/commits/{ref}/{filepath}",
        "commit_path": "/commit/{last_commit}",
    }
}


def _get_git_file_info(
    repo: Repository, project_relative_path: Path
) -> GitFileInfo | None:
    walker = repo.walk(repo.head.target, GIT_SORT_TIME)
    commit = next((c for c in walker if str(project_relative_path) in c.tree), None)

    if not commit:
        return

    return GitFileInfo(
        commit_sha=str(commit.id)[:7],
        committed_at=datetime.datetime.fromtimestamp(
            commit.commit_time, datetime.timezone.utc
        ),
    )


def _render_footer(path_info: PathInfo, ctx: BuildContext) -> str:
    git_file_info = (
        _get_git_file_info(ctx.repo, path_info.project_relative_path)
        if ctx.repo
        else None
    )
    last_modified = (
        git_file_info.committed_at.strftime("%Y-%m-%d %H:%M:%S")
        if git_file_info
        else "unknown"
    )

    path_template_context = {
        "ref": ctx.git_ref,
        "filepath": path_info.project_relative_path,
        "last_commit": git_file_info.commit_sha if git_file_info else None,
    }
    path_templates = PATH_TEMPLATES_BY_PROVIDER.get(ctx.git_provider)
    assert path_templates, f"Path templates not defined for provider {ctx.git_provider}"

    if not ctx.git_url_base:
        if git_file_info:
            return f"Last modified: {last_modified}"
        return ""

    edit_url = urljoin(
        ctx.git_url_base, path_templates["edit_path"].format(**path_template_context)
    )
    history_url = urljoin(
        ctx.git_url_base, path_templates["history_path"].format(**path_template_context)
    )

    last_modified_link = ""
    if git_file_info:
        commit_url = urljoin(
            ctx.git_url_base,
            path_templates["commit_path"].format(**path_template_context),
        )
        last_modified_link = f" | [{last_modified}]({commit_url})"

    return (
        f"[View source]({edit_url}) | [View history]({history_url}){last_modified_link}"
    )


def add_footer(path_info: PathInfo, ctx: BuildContext, content: str) -> str:
    footer = _render_footer(path_info, ctx)
    if not footer:
        return content
    separator = "\n* * *\n\n"
    return content + separator + footer


def convert_gemoji(path_info: PathInfo, ctx: BuildContext, content: str) -> str:
    script_path = Path(__file__).parent / "scripts" / "convert-gemoji-to-unicode.mjs"
    return apply_external_processor(path_info, ctx, script_path, content)


def apply_external_processor(
    path_info: PathInfo, ctx: BuildContext, processor_path: Path, content: str | bytes
) -> str:
    content = content.encode("utf8") if isinstance(content, str) else content
    return subprocess.run(
        [processor_path],
        input=content,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.decode("utf8")


class Builtin(enum.Enum):
    noop = enum.auto()
    add_footer = enum.auto()
    convert_gemoji = enum.auto()


BUILTINS = {
    Builtin.noop: noop,
    Builtin.add_footer: add_footer,
    Builtin.convert_gemoji: convert_gemoji,
}


@dataclasses.dataclass
class External:
    path: Path


@dataclasses.dataclass
class ProcessorParam:
    raw_value: str
    ext: str
    processor: Builtin | External | None = None
    copy_from_ext: str | None = None


class ProcessorParamType(click.ParamType):
    name = "processor"

    BUILTIN_MARKER = "builtin"
    DEFAULT_EXTENSION = "md"

    def convert(self, value, param, ctx):
        parts = value.split(":", 3)
        ext = self.DEFAULT_EXTENSION
        processor_path = None
        builtin_name = None
        copy_from_ext = None
        path_type = click.Path(
            exists=True,
            dir_okay=False,
            resolve_path=True,
            path_type=Path,
            executable=True,
        )
        if len(parts) == 1:
            processor_path = cast(Path, path_type.convert(parts[0], param, ctx))

        if len(parts) == 2:
            ext_or_builtin, bare_value = parts
            if ext_or_builtin == self.BUILTIN_MARKER:
                builtin_name = bare_value
            else:
                ext = ext_or_builtin

                try:
                    processor_path = cast(
                        Path, path_type.convert(bare_value, param, ctx)
                    )
                except click.BadParameter:
                    copy_from_ext = bare_value

        if len(parts) == 3:
            ext, marker, bare_value = parts
            if marker != self.BUILTIN_MARKER:
                self.fail(
                    f"Expected value of format '<processor-path>', 'builtin:<builtin-name>', '<ext>:<processor-path>, or '<ext>:builtin:<builtin-name>', not {value}",
                    param,
                    ctx,
                )
            builtin_name = bare_value

        if builtin_name:
            try:
                builtin = getattr(Builtin, builtin_name)
                return ProcessorParam(raw_value=value, ext=ext, processor=builtin)
            except AttributeError:
                valid_names = [m.name for m in Builtin]
                self.fail(
                    f"'{builtin_name}' is not a builtin processor name; must be one of {', '.join(valid_names)}",
                    param,
                    ctx,
                )

        if processor_path:
            return ProcessorParam(
                raw_value=value, ext=ext, processor=External(path=Path(processor_path))
            )

        if copy_from_ext:
            return ProcessorParam(raw_value=value, ext=ext, copy_from_ext=copy_from_ext)

        self.fail("Could not parse value", param, ctx)


DEFAULT_STACK = ("builtin:convert_gemoji", "builtin:add_footer")
