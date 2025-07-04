import dataclasses
import enum
from pathlib import Path

from pygit2.repository import Repository


class GitProvider(enum.Enum):
    GITHUB = enum.auto()


@dataclasses.dataclass
class PathInfo:
    project_relative_path: Path
    absolute_source_path: Path
    absolute_build_path: Path


@dataclasses.dataclass
class BuildContext:
    build_dir: Path
    project_root: Path
    repo: Repository | None
    git_url_base: str | None
    git_provider: GitProvider
    git_ref: str

    def get_source_path_info(
        self, source_dir: Path, project_relative_path: Path
    ) -> PathInfo:
        absolute_source_path = self.project_root / project_relative_path
        relative_source_path = absolute_source_path.relative_to(source_dir)
        absolute_build_path = self.build_dir / relative_source_path
        return PathInfo(
            project_relative_path=project_relative_path,
            absolute_source_path=absolute_source_path,
            absolute_build_path=absolute_build_path,
        )
