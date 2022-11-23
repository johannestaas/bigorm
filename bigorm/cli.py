import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", "-m", default="hello python package")
    args = parser.parse_args()
    print(args.message)
