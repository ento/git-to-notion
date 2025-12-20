from unittest import mock

import pytest
from click.testing import CliRunner
from git_to_notion.cli import cli


@pytest.fixture
def runner():
    return CliRunner(catch_exceptions=False)


def test_build_with_default_processors(tmp_path, runner):
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    images_dir = source_dir / "images"
    images_dir.mkdir()

    (source_dir / "README.md").write_text("Welcome! :star:")
    (images_dir / "logo.png").write_text("Logo")

    build_dir = tmp_path / "build"

    result = runner.invoke(cli, ["build", str(source_dir), str(build_dir)])

    assert result.exit_code == 0, result.output

    assert (build_dir / "README.md").read_text() == "Welcome! ⭐\n"
    assert (build_dir / "images" / "logo.png").read_text() == "Logo"


def test_build_with_gitignore(tmp_path, runner):
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    (source_dir / "README.md").write_text("Welcome! :star:")
    (source_dir / "TODO.md").write_text("TODO")
    (source_dir / ".gitignore").write_text("TODO.md")

    build_dir = tmp_path / "build"

    result = runner.invoke(cli, ["build", str(source_dir), str(build_dir)])

    assert result.exit_code == 0, result.output

    assert (build_dir / "README.md").read_text() == "Welcome! ⭐\n"
    assert not (build_dir / "TODO.md").exists()


def test_build_with_symlinks(tmp_path, runner):
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    (source_dir / "README.md").write_text("Welcome! :star:")
    (source_dir / "ignored_file_a.md").write_text("ignored_a")
    (source_dir / "ignored_file_b.md").write_text("ignored_b")
    (source_dir / "included_symlink_to_ignored_file").symlink_to("ignored_file_a.md")
    (source_dir / "ignored_symlink").symlink_to("ignored_file_b.md")
    (source_dir / ".gitignore").write_text(
        "\n".join(["ignored_file*", "ignored_symlink*"])
    )

    build_dir = tmp_path / "build"

    result = runner.invoke(cli, ["build", str(source_dir), str(build_dir)])

    assert result.exit_code == 0, result.output

    assert (build_dir / "README.md").is_file()
    assert not (build_dir / "ignored_file_a.md").exists()
    assert not (build_dir / "ignored_file_b.md").exists()
    assert (build_dir / "included_symlink_to_ignored_file").read_text() == "ignored_a"


def test_sync(tmp_path, runner):
    build_dir = tmp_path / "build"

    with mock.patch("os.execvp") as mock_execvp:
        result = runner.invoke(
            cli, ["sync", str(build_dir), "-t", "NOTION_TOKEN", "-p", "NOTION_PAGE_ID"]
        )

        assert result.exit_code == 0, result.output
        assert mock_execvp.call_args.args == (
            "md-to-notion",
            [
                "md-to-notion",
                "--timeout",
                "30000",
                str(build_dir),
                "-t",
                "NOTION_TOKEN",
                "-p",
                "NOTION_PAGE_ID",
                "-d",
            ],
        )
