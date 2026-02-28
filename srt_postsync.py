#!/usr/bin/env python

"""srt_presync.py
A script to compile separate video, audio, and subtitle streams
into a .mp4 movie file.

- ffmpeg for compilation of streams
"""

import subprocess

from pathlib import Path
from typing_extensions import Annotated

import typer

from rich import print  # type: ignore
from rich.progress import Progress, SpinnerColumn, TextColumn  # type: ignore

app = typer.Typer()

# Typer argument/option types
OPT_ARG_TYPE_VIDEOPATH = Annotated[
    Path, typer.Option("--videopath", help="Path to video stream")
]

OPT_ARG_TYPE_AUDIOPATHS = Annotated[
    str, typer.Option("--audiopaths", help="Paths to audio streams")
]

OPT_ARG_TYPE_SUBSPATHS = Annotated[
    str, typer.Option("--subspaths", help="Paths to subtitle files")
]

OPT_ARG_TYPE_OUTDIR = Annotated[
    Path, typer.Option("--outdir", help="Output directory for compiled movie")
]

OPT_ARG_TYPE_OUTSTEM = Annotated[
    str, typer.Option("--outstem", help="Filestem for output movie")
]

OPT_ARG_TYPE_TITLE = Annotated[
    str, typer.Option("--title", help="Title to embed in compiled video")
]

OPT_ARG_TYPE_AUDIOLANGS = Annotated[
    str, typer.Option("--audiolangs", help="Language abbreviations for audio tracks")
]

OPT_ARG_TYPE_SUBSLANGS = Annotated[
    str, typer.Option("--subslangs", help="Language abbreviations for subtitle tracks")
]


def check_dependencies() -> bool:
    """Return True if dependencies are present, false otherwise"""
    result = True

    # Check for ffmpeg
    cmd = ["ffmpeg", "-version"]
    res = subprocess.run(cmd, capture_output=True)
    if not res.stdout.startswith(b"ffmpeg version"):
        print("ffmpeg not found")
        result = False
    else:
        stdout_split = res.stdout.decode().split("\n")
        print(f"Found {stdout_split[0]}")

    return result  # No checks failed


def compile_movie(
    outpath: Path,
    videopath: Path,
    audiopaths: list[Path],
    subspaths: list[Path],
    title: str = "",
    audiolangs: list[str] = [],
    subslangs: list[str] = [],
) -> Path:
    """Compile streams to .mp4 format using ffmpeg"""
    cmd = ["ffmpeg"]

    # Add video stream
    inputs = ["-i", str(videopath)]
    maps = ["-map", "0:v:0"]
    metadata = []

    # Add audio streams
    for audiotrack, audiopath in enumerate(audiopaths):
        inputs += ["-i", str(audiopath)]
        maps += ["-map", f"{audiotrack + 1}:a:0"]
        if len(audiolangs):
            metadata += [
                f"-metadata:s:{audiotrack + 1}",
                f"language={audiolangs[audiotrack]}",
            ]

    # Add subtitle streams
    for substrack, subspath in enumerate(subspaths):
        inputs += ["-i", str(subspath)]
        maps += ["-map", f"{substrack + len(audiopaths) + 1}:s:0"]
        if len(subslangs):
            metadata += [
                f"-metadata:s:s:{substrack}",
                f"language={subslangs[substrack]}",
            ]

    # Add inputs and maps
    cmd += inputs + maps

    # Add codec parameters
    cmd += ["-c:v", "copy", "-c:a", "libfdk_aac", "-c:s", "mov_text"]

    # Add metadata
    cmd += ["-metadata", f'title="{title}"'] + metadata

    # Add outputs
    cmd += ["-y", str(outpath)]

    print(str(" ".join(cmd)))

    res = subprocess.run(cmd, capture_output=True)

    if 0 == res.returncode:
        print(res.stderr.decode())
    else:
        raise Exception(f"Compiling streams to {outpath} failed")

    return outpath


@app.command()
def main(
    videopath: OPT_ARG_TYPE_VIDEOPATH,
    audiopathstrs: OPT_ARG_TYPE_AUDIOPATHS,
    subspathstrs: OPT_ARG_TYPE_SUBSPATHS = "",
    outdir: OPT_ARG_TYPE_OUTDIR = Path("."),
    outstem: OPT_ARG_TYPE_OUTSTEM = "movie",
    title: OPT_ARG_TYPE_TITLE = "srt_postsync compiled movie",
    audiolangstrs: OPT_ARG_TYPE_AUDIOLANGS = "",
    subslangstrs: OPT_ARG_TYPE_SUBSLANGS = "",
) -> None:
    """Entry point for sre_postsync"""
    # Check that dependencies (mkvtoolnix, ffmpeg) are present
    if not check_dependencies():
        raise Exception(
            "Exiting due to missing dependency. Please ensure that ffmpeg is installed"
        )

    # Convert inputs to paths, where needed
    print("Received input paths")
    print(f"\tVideo: {videopath}")
    audiopaths = [Path(_) for _ in audiopathstrs.split(",")]
    print(f"\tAudio:\n{''.join('\t\t' + str(_) + '\n' for _ in audiopaths)}")
    if len(subspathstrs):
        subspaths = [Path(_) for _ in subspathstrs.split(",")]
        print(f"\tSubtitles:\n{''.join('\t\t' + str(_) + '\n' for _ in subspaths)}")

    # Identify audio and subtitle languages
    if len(audiolangstrs):
        audiolangs = [str(_) for _ in audiolangstrs.split(",")]
        if len(audiolangs) != len(audiopaths):
            raise Exception(
                f"Number of audio languages (found {len(audiolangs)}) must match number of audio files (found {len(audiopaths)})"
            )
    if len(subslangstrs):
        subslangs = [str(_) for _ in subslangstrs.split(",")]
        if len(subslangs) != len(subspaths):
            raise Exception(
                f"Number of subtitle languages (found {len(audiolangs)}) must match number of subtitle files (found {len(audiopaths)})"
            )

    # If outpath doesn't exist, make it
    outdir.mkdir(parents=True, exist_ok=True)

    # Compile streams into a movie
    outpath = (outdir / outstem).with_suffix(".mp4")
    if outpath.exists():
        print(f"File {outpath} already exists, not converting")
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Compiling streams to {outpath}", total=None)
            compile_movie(
                outpath, videopath, audiopaths, subspaths, title, audiolangs, subslangs
            )
            print(f"Compiled streams to {outpath}")


if __name__ == "__main__":
    app()
