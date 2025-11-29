import argparse


def mm(inches: float) -> float:
    return 24.1 * inches


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inches", type=float)
    args = parser.parse_args()

    print(mm(args.inches))
