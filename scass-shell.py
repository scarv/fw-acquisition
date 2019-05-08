#!/usr/bin/python3

import scass

def main():
    
    # Connect to the first picoscope5000 we find.
    scope   = scass.scope.Picoscope5000()

    info    = scope.scope_information

    print(info)

if(__name__ == "__main__"):
    main()

