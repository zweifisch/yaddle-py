import sys
import json
import yaddle


def main():
    if len(sys.argv) == 1:
        infile = sys.stdin
        outfile = sys.stdout
    elif len(sys.argv) == 2:
        infile = open(sys.argv[1], 'rb')
        outfile = sys.stdout
    elif len(sys.argv) == 3:
        infile = open(sys.argv[1], 'rb')
        outfile = open(sys.argv[2], 'wb')
    else:
        raise SystemExit(sys.argv[0] + " [infile [outfile]]")
    with infile:
        try:
            obj = yaddle.load(infile)
        except ValueError, e:
            raise SystemExit(e)
    with outfile:
        json.dump(obj, outfile, sort_keys=True,
                  indent=4, separators=(',', ': '))
        outfile.write('\n')


if __name__ == '__main__':
    main()
