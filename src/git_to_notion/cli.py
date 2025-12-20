import os
import shutil
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Iterator

import click
from gitignore_parser import parse_gitignore
from pygit2.repository import Repository

from . import processors
from .types import BuildContext, GitProvider, PathInfo


def find_repo_root(start_dir: Path) -> Path | None:
    current_dir = start_dir
    while not (current_dir / ".git").is_dir():
        if str(current_dir) == current_dir.anchor:
            return
        current_dir = current_dir.parent
    return current_dir.absolute().resolve()


def list_source_files(
    source_dir: Path, project_root: Path, gitignore_path: Path | None
) -> Iterator[tuple[Path, Path]]:
    should_ignore = None
    if gitignore_path:
        should_ignore = parse_gitignore(gitignore_path)
    for dirpath, dirnames, filenames in source_dir.walk():
        for filename in filenames:
            filepath = dirpath / filename
            if should_ignore and should_ignore(filepath):
                continue

            content_path = filepath
            if filepath.is_symlink():
                content_path = filepath.resolve()
                if not (
                    content_path.is_file() and content_path.is_relative_to(project_root)
                ):
                    continue

            yield filepath.relative_to(project_root), content_path


def process_file(
    path_info: PathInfo,
    ctx: BuildContext,
    preprocessors: Sequence[processors.Builtin | processors.External],
) -> bytes:
    content = path_info.absolute_content_path.read_bytes()
    for processor in preprocessors:
        match processor:
            case processors.Builtin():
                content = (
                    content.decode("utf8") if isinstance(content, bytes) else content
                )
                content = processors.BUILTINS[processor](path_info, ctx, content)
            case processors.External(path=processor_path):
                content = processors.apply_external_processor(
                    path_info, ctx, processor_path, content
                )

    content = content.encode("utf8") if isinstance(content, str) else content
    return content


@click.group()
def cli():
    pass


@cli.command()
@click.argument(
    "source_dir",
    type=click.Path(file_okay=False, exists=True, resolve_path=True, path_type=Path),
)
@click.argument(
    "build_dir",
    type=click.Path(file_okay=False, writable=True, resolve_path=True, path_type=Path),
)
@click.option("--gitignore/--no-gitignore", default=True)
@click.option("--git-url-base")
@click.option(
    "--git-provider",
    default="github",
    type=click.Choice(GitProvider, case_sensitive=False),
)
@click.option("--git-ref", default="HEAD")
@click.option(
    "-p",
    "--preprocess",
    multiple=True,
    default=processors.DEFAULT_STACK,
    type=processors.ProcessorParamType(),
)
def build(
    source_dir, build_dir, gitignore, git_url_base, git_provider, git_ref, preprocess
):
    repo_root = find_repo_root(source_dir)
    project_root = repo_root or source_dir

    gitignore_path = None
    if gitignore:
        if project_root.joinpath(".gitignore").is_file():
            gitignore_path = project_root.joinpath(".gitignore")

    ctx = BuildContext(
        build_dir=build_dir,
        project_root=project_root,
        repo=Repository(str(repo_root)) if repo_root else None,
        git_url_base=git_url_base,
        git_provider=git_provider,
        git_ref=git_ref,
    )

    shutil.rmtree(ctx.build_dir, ignore_errors=True)

    preprocessors_by_extension: dict[
        str, list[processors.Builtin | processors.External]
    ] = defaultdict(list)
    copy_from_ext = []
    for param in preprocess:
        if param.copy_from_ext:
            copy_from_ext.append(param)
        elif param.processor:
            preprocessors_by_extension[param.ext].append(param.processor)
        else:
            click.secho(
                f"A parsed --processor param specifies neithr copy_from_ext nor processor: {param}"
            )
    for param in copy_from_ext:
        preprocessors_by_extension[param.ext] = list(
            preprocessors_by_extension[param.copy_from_ext]
        )

    for project_relative_path, absolute_content_path in list_source_files(
        source_dir, ctx.project_root, gitignore_path
    ):
        path_info = ctx.get_source_path_info(
            source_dir, project_relative_path, absolute_content_path
        )
        ext = project_relative_path.suffix.lstrip(".")

        click.secho(f"processing: {project_relative_path}")
        preprocessors = preprocessors_by_extension[ext]
        content = process_file(path_info, ctx, preprocessors)

        path_info.absolute_build_path.parent.mkdir(parents=True, exist_ok=True)
        path_info.absolute_build_path.write_bytes(content)


@cli.command()
@click.argument("build_dir", type=click.Path(file_okay=False, writable=True))
@click.option("-p", "--notion-page-id", required=True, envvar="NOTION_PAGE_ID")
@click.option("-t", "--notion-token", required=True, envvar="NOTION_TOKEN")
def sync(build_dir: Path, notion_page_id: str, notion_token: str):
    command = ["md-to-notion"]
    flags = [
        "--timeout",
        "30000",
        build_dir,
        "-t",
        notion_token,
        "-p",
        notion_page_id,
        "-d",
    ]
    os.execvp("md-to-notion", command + flags)


if __name__ == "__main__":
    cli()
