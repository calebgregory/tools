#!/usr/bin/env python

import sys
from datetime import datetime
from math import floor
from time import sleep
import readline

def main():
    start = datetime.utcnow()

    print(f'starting at {start.isoformat()}')

    while True:
        sleep(1)
        now = datetime.utcnow()
        duration = now - start
        s = duration.seconds
        min, sec = floor(s / 60), s % 60

        sys.stdout.write(f"\r{str(min).zfill(2)}:{str(sec).zfill(2)} ")
        sys.stdout.flush()


if __name__ == '__main__':
    main()

