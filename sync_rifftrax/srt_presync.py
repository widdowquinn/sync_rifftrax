#!/usr/bin/env python

"""srt_presync.py
A script to extract separate video, audio, and subtitle streams
from a movie file.

Video is extracted to .mkv
Audio is extracted to .ac3 and .wav
Subtitles are extracted to .ass

This tool depends on the presence of

- ffmpeg for movie conversion to mkv
- mkvtoolnix for audio and subtitle extraction
- ffmpeg for audio conversion to wav
"""

import subprocess

from collections import defaultdict
from pathlib import Path
from typing_extensions import Annotated

import typer

from rich import print  # type: ignore
from rich.progress import Progress, SpinnerColumn, TextColumn  # type: ignore

app = typer.Typer()

# Typer argument/option types
OPT_ARG_TYPE_MOVIEPATH = Annotated[
    Path, typer.Option("--moviepath", help="Path to movie for extraction")
]

OPT_ARG_TYPE_OUTPATH = Annotated[
    Path, typer.Option("--outpath", help="Directory for output files")
]

OPT_ARG_TYPE_OUTSTEM = Annotated[
    str, typer.Option("--outstem", help="Stem for output files")
]


def check_dependencies() -> bool:
    """Return True if dependencies are present, false otherwise"""
    result = True

    # Check for mkvtoolnix
    cmd = ["mkvinfo", "-V"]
    res = subprocess.run(cmd, capture_output=True)
    if not res.stdout.startswith(b"mkvinfo v"):
        print("mkvtoolnix not found")
        result = False
    else:
        print(f"Found {res.stdout.decode().strip()}")

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


def convert_audio(streampath: Path, wavpath: Path) -> Path:
    """Convert audio to .wav format using ffmpeg"""
    cmd = [
        "ffmpeg",
        "-i",
        str(streampath),
        "-ac",  # enforce audio channels
        "2",  # mixdown to stereo (if needed)
        str(wavpath),
    ]
    res = subprocess.run(cmd, capture_output=True)

    if 0 == res.returncode:
        print(res.stderr.decode())
    else:
        raise Exception(f"Converting {streampath} to {wavpath} failed")

    return wavpath


def convert_movie(moviepath: Path, mkvpath: Path) -> Path:
    """Convert movie to .mkv format using ffmpeg"""
    cmd = [
        "ffmpeg",
        "-i",
        str(moviepath),
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        str(mkvpath),
    ]
    res = subprocess.run(cmd, capture_output=True)

    if 0 == res.returncode:
        print(res.stderr.decode())
    else:
        raise Exception(f"Converting {moviepath} to {mkvpath} failed")

    return mkvpath


def identify_tracks(mkvpath: Path) -> dict[str, list[int]]:
    """Return the track IDs for video, audio, and subtitles"""
    tracks = defaultdict(list)  # track number, keyed by track type

    cmd = ["mkvinfo", str(mkvpath)]
    res = subprocess.run(cmd, capture_output=True)

    # Parse stdout to identify tracks
    parsing_track, parsing_type = True, False
    for line in res.stdout.decode().split("\n"):
        if parsing_track and "Track number" in line:
            tracknum = int(line.split()[-1][0])
            parsing_type = True
        if parsing_type and "Track type" in line:
            tracktype = line.split()[-1]
            tracks[tracktype].append(tracknum)
            print(f"\tTrack {tracknum}: {tracktype}")

    return tracks


def extract_tracks(
    mkvpath: Path, tracks: dict[str, list[int]]
) -> dict[str, list[Path]]:
    """Return dictionary of paths to streams"""
    mkvstem = mkvpath.with_suffix("")
    streampaths = defaultdict(list)

    cmd = ["mkvextract", "tracks", str(mkvpath)]

    # Extend command-line with audio, and subtitle paths
    # We use the first audio track
    audiopath = mkvpath.with_suffix(".ac3")
    streampaths["audio"].append(audiopath)
    cmd += [f"{min(tracks['audio'])}:{audiopath}"]
    # We retain all subtitle tracks, if any exist
    for tracknum in tracks["subtitles"]:
        subspath = Path(str(mkvstem) + "_subs" + str(tracknum) + ".ass")
        cmd += [f"{tracknum}:{subspath}"]
        streampaths["subtitles"].append(subspath)

    res = subprocess.run(cmd, capture_output=True)
    if 0 != res.returncode:
        print(res.stderr)

    return streampaths


@app.command()
def main(
    moviepath: OPT_ARG_TYPE_MOVIEPATH,
    outpath: OPT_ARG_TYPE_OUTPATH = Path("."),
    outstem: OPT_ARG_TYPE_OUTSTEM = "movie",
) -> None:
    """Entry point for sre_presync"""
    # Check that dependencies (mkvtoolnix, ffmpeg) are present
    if not check_dependencies():
        raise Exception(
            "Exiting due to missing dependency. Please ensure that ffmpeg and mkvtoolnix are installed"
        )

    # If outpath doesn't exist, make it
    outpath.mkdir(parents=True, exist_ok=True)

    # Convert movie to .mkv
    mkvpath = (outpath / outstem).with_suffix(".mkv")
    if mkvpath.exists():
        print(f".mkv file {mkvpath} already exists, not converting")
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Converting {moviepath} to .mkv", total=None)
            convert_movie(moviepath, mkvpath)
            print(f"Converted {moviepath} to {mkvpath}")

    # Identify tracks in .mkv
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=f"Identifying tracks in {mkvpath}", total=None)
        tracks = identify_tracks(mkvpath)

    # Extract tracks from .mkv
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=f"Extracting tracks from {mkvpath}", total=None)
        streampaths = extract_tracks(mkvpath, tracks)

    # Convert moviaudio to .wav
    wavpath = (outpath / outstem).with_suffix(".wav")
    if wavpath.exists():
        print(f".wav file {wavpath} already exists, not converting")
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(
                description=f"Converting {streampaths['audio'][0]} to .wav", total=None
            )
            convert_audio(streampaths["audio"][0], wavpath)
            print(f"Converted {streampaths['audio'][0]} to {wavpath}")

    print("Conversion complete")


if __name__ == "__main__":
    app()
