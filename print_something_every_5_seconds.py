import time
from datetime import datetime, timedelta

def main():
    start = datetime.utcnow()
    while True:
        time.sleep(5)
        dur = datetime.utcnow() - start
        print(f'been counting for {dur}')

if __name__ == '__main__':
    main()
