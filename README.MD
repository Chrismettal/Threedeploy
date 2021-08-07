# Python-Thingideploy

![Logo](img/Logo.png)

Python app to automatically deploy a project to Thingiverse.

If you like my work please consider supporting my caffeine addiction!

<a href='https://ko-fi.com/U7U6G0X3' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://az743702.vo.msecnd.net/cdn/kofi4.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

## Expected folder structure

The program expects files in the following structure:

- `/YourProjectFolder` - Path that is input as command line argument, `thingideploy.py /home/user/MyProjectFolder`
  - `/gcode`    - Location for sliced gcode files
  - `/img`      - Location for images
  - `/source`   - Location for project source file, FreeCAD, OpenSCAD project file etc.
  - `/3d`       - Location for printable 3d files like stl, obj etc.