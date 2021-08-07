#!/usr/bin/python
import argparse
import json

def main():
    ##########################################################################
    ##                            Arguments                                 ##
    ##########################################################################

    # path
    parser = argparse.ArgumentParser(description='Upload 3D printing project to Thingiverse automatically')
    parser.add_argument('path', type=str, nargs='?',
                        help='Path to expected folder structure')
    args = parser.parse_args()
    
    # generate error if no path provided, no sanity check on type of path argument yet
    if not (args.path):
        parser.error('No path provided, please call with "thingideploy.py <PathToExpectedFileStructure>"')

    projectpath = args.path

    ##########################################################################
    ##                               Init                                   ##
    ##########################################################################

    # Intro message
    print()
    print("Starting Thingideploy with project path:")
    print(projectpath)
    print()

    ##########################################################################
    ##                          File parsing                                ##
    ##########################################################################

    # Description
    descpath = projectpath + "/README.md"
    with open(descpath, "r", encoding="utf-8") as f:
        desc = f.read()
        print("Description: ")
        print(desc)
        print()

    # Tags
    tagpath = projectpath + "/tags.md"
    with open(tagpath, "r", encoding="utf-8") as f:
        tags = f.read()
        print("Tags: ")
        print(tags)
        print()

    # Flags
    flagpath = projectpath + "/flags.json"
    with open(flagpath, "r", encoding="utf-8") as f:
        flags = json.load(f)
        print("Flags: ")
        print(flags)
        print()


    ##########################################################################
    ##                     Thingiverse deployment                           ##
    ##########################################################################

    


##########################################################################
##                        main() idiom                                  ##
##########################################################################
if __name__ == '__main__':
    main()


