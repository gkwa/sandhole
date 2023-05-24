import argparse
import pathlib
import sys
import time

import platformdirs
import yaml


def parse_timestamp(timestamp):
    unit = timestamp[-1]
    value = int(timestamp[:-1])

    if unit == "h":
        return value * 60 * 60
    elif unit == "d":
        return value * 24 * 60 * 60
    elif unit == "w":
        return value * 7 * 24 * 60 * 60
    elif unit == "m":
        return value * 30 * 24 * 60 * 60
    elif unit == "y":
        return value * 365 * 24 * 60 * 60
    else:
        raise argparse.ArgumentTypeError(
            "Invalid timestamp unit. Use h, d, w, m, or y."
        )


def resolve_path(path):
    resolved_path = pathlib.Path(path).expanduser()
    return resolved_path


def main(args):
    current_time = time.time()
    threshold = current_time - args.age

    list_file = resolve_path(args.list_file)

    if not list_file.exists():
        print(f"File not found: {list_file}", file=sys.stderr)
        sys.exit(1)

    ignore_list = []

    ignore_list.extend(args.append_ignore)

    config_dir = pathlib.Path(platformdirs.user_config_dir("sandhole"))
    config_file = pathlib.Path(config_dir, "config.yaml")

    if not config_file.exists():
        # Create a sample config file with example ignore_list
        sample_config = {"ignore_list": ignore_list}
        config_dir.mkdir(parents=True, exist_ok=True)
        with config_file.open("w") as file:
            yaml.safe_dump(sample_config, file)

    else:
        with config_file.open("r") as file:
            config = yaml.safe_load(file)
            if config and "ignore_list" in config:
                ignore_list.extend(config["ignore_list"])

    with list_file.open("r") as file:
        file_paths = file.read().splitlines()

    for file_path in file_paths:
        path = resolve_path(file_path)
        if not path.exists() and path.name not in ignore_list:
            print(f"File not found: {path}", file=sys.stderr)
        elif (
            path.is_file()
            and path.stat().st_mtime >= threshold
            and path.name not in ignore_list
        ):
            print(file_path)


if __name__ == "__main__":
    main()
