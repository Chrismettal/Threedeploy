#!/usr/bin/python
import argparse
import json
import os

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

    # 3D files
    threedpath = projectpath + "/3d"
    threedfiles = []
    for file in os.listdir(threedpath):
        if (file.endswith(".stl")  or
            file.endswith(".obj")  or
            file.endswith(".stp")  or
            file.endswith(".STEP") or
            file.endswith(".3mf")):
            threedfiles.append(os.path.join(threedpath, file))

    print("Found 3D files: ")
    for file in threedfiles:
        print(file)
    print()

    # Gcodes
    gcodepath = projectpath + "/gcode"
    gcodefiles = []
    for file in os.listdir(gcodepath):
        if (file.endswith(".gcode")):
            gcodefiles.append(os.path.join(gcodepath, file))

    print("Found gcode files: ")
    for file in gcodefiles:
        print(file)
    print()


    # Images
    imgpath = projectpath + "/img"
    imgfiles = []
    for file in os.listdir(imgpath):
        if (file.endswith(".png")  or
            file.endswith(".jpg")  or
            file.endswith(".bmp")):
            imgfiles.append(os.path.join(imgpath, file))

    print("Found image files: ")
    for file in imgfiles:
        print(file)
    print()


    ##########################################################################
    ##                     Thingiverse deployment                           ##
    ##########################################################################




##########################################################################
##                        main() idiom                                  ##
##########################################################################
if __name__ == '__main__':
    main()


