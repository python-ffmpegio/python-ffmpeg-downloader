import argparse
import ffmpeg_downloader as ffdl
import tqdm

parser = argparse.ArgumentParser(description="Download latest FFmpeg release build")
parser.add_argument(
    "--update", "-U", "-u", action="store_true", help="Update to the latest release"
)
parser.add_argument(
    "--remove",
    "-r",
    "-R",
    "--delete",
    "-d",
    "-D",
    action="store_true",
    help="Remove downloaded FFmpeg build",
)

args = parser.parse_args()

ver = ffdl.ffmpeg_version

if args.remove:
    if ver is None:
        print("\nNo FFmpeg build has been downloaded.")
    elif input(f"\nAre you sure to remove the FFmpeg build v{ver}? [yN]: ").lower() in (
        "y",
        "yes",
    ):
        try:
            ffdl.remove(ignore_errors=False)
            print("\nFFmpeg build successfully removed.")
        except:
            print(
                f"\nFailed to delete FFmpeg build in {ffdl.ffmpeg_dir}. Please manually remove the directory."
            )
    else:
        print("\nFFmpeg build removal canceled.")
elif ver is None or args.update or ffdl.has_update():
    prog_data = {}
    try:

        def progress(nread, nbytes):
            if not len(prog_data):
                prog_data["tqdm"] = tqdm.tqdm(
                    desc="downloading", total=nbytes, unit=" bytes", leave=False
                )
                prog_data["last"] = 0
            pbar = prog_data["tqdm"]
            pbar.update(nread - prog_data["last"])
            prog_data["last"] = nread

        if ffdl.update(progress=progress):
            print("\nLatest version")
        else:
            print(f"FFmpeg v{ffdl.ffmpeg_version} successfully installed in {ffdl.ffmpeg_dir}\n")
    finally:
        pbar = prog_data.get("tqdm", None)
        if pbar:
            pbar.close()
else:
    print(f"FFmpeg v{ffdl.ffmpeg_version} already installed")
