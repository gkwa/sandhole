import argparse
import datetime
import pathlib
import re
import sys
import tempfile
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


def format_file_list(input_file, output_file):
    with open(output_file, "w") as outfile:
        with open(input_file, "r") as infile:
            lines = infile.readlines()

        for line in lines:
            file_path = line.strip()
            path = pathlib.Path(file_path)
            if path.exists():
                mtime = path.stat().st_mtime
                mtime_str = datetime.datetime.fromtimestamp(mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                outfile.write(f"{mtime_str} {file_path}\n")
            else:
                print(f"File not found: {file_path}\n", sys.stderr)

    with open(output_file, "r") as infile:
        lines = infile.readlines()

    lines.sort(
        key=lambda line: datetime.datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S"),
        reverse=True,
    )

    with open(input_file, "w") as outfile:
        for line in lines:
            outfile.write(line)


def parse_line(line):
    index = line.find("/")
    if index != -1:
        timestamp_str = line[:index].strip()
        path = line[index:].strip()
    else:
        timestamp_str = line.strip()
        path = ""

    timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

    return timestamp, path


def process_file_until_timestamp(input_file, stop_timestamp):
    with open(input_file, "r") as infile:
        for line in infile:
            timestamp, file_path = parse_line(line)
            path = pathlib.Path(file_path)
            if not path.exists():
                print(f"File not found: {file_path}", file=sys.stderr)
                continue

            if timestamp < stop_timestamp:
                break
            print(file_path)


def is_file_sorted(file_path):
    with open(file_path, "r") as file:
        for i, line in enumerate(file):
            if i >= 10:
                break
            line = line.strip()
            if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} .+$", line):
                return False
    return True


def main(args):
    current_time = time.time()
    threshold = current_time - args.age
    threshold = datetime.datetime.fromtimestamp(threshold)

    list_file = resolve_path(args.list_file)

    if not is_file_sorted(list_file):
        temp_file_path = pathlib.Path(tempfile.mkstemp()[1])
        format_file_list(list_file, temp_file_path)

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

    process_file_until_timestamp(list_file, threshold)


if __name__ == "__main__":
    main()
