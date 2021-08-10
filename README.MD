# Thingideploy

Python app to automatically deploy a project to Thingiverse. Can be used manually, but is really supposed to be used via GitLab CI/CD or Github Actions for example.

Providing the correct project structure, Thingideploy will do the following:
- Read Thing metadata from `thingdata.json`
- Create a Thing based on your provided data, or patch an existing one
- Update the name, tags, ~~description~~ (currently broken on Thingi side apparently), license, category and WIP state of your thing
- Publish your thing, if flag is set
- Upload found 3D files / known project source files, or replace existing ones if local files have been modified since upload
- Upload found images or replace existing ones

---

:construction: :construction: :construction:

### WIP WARNING

This project is early work in progress. While Thing creation and deploying works, automatic API token and project generation is not yet implemented. Logging and error handling is more of a suggestion right now. This is basically only released so I can use it already in other pipelines.

This Readme especially is being updated with usage instructions in the coming days.

:construction: :construction: :construction:

---

If you like my work please consider supporting my caffeine addiction!

<a href='https://ko-fi.com/U7U6G0X3' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://az743702.vo.msecnd.net/cdn/kofi4.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

## Usage

### Project creation mode 

Not yet implemented, will create expected folder structure in your given location

### API token request mode

Not yet implemented, will request access to your account, providing you with an API token to be used as an argument for later project deployment.

### Deployment mode

Actual project deployment, executed with:

```bash
thingideploy.py <PathToExpectedFolderStructure> --deploy-project=<YourApiToken> 
```

## Expected folder structure

The program expects files in the following structure:

- `/YourProjectFolder` - Path that is input as command line argument, `thingideploy.py /home/user/MyProjectFolder`
  - `/gcode`    - Location for sliced gcode files
  - `/img`      - Location for images
  - `/source`   - Location for project source file, FreeCAD, OpenSCAD project file etc.
  - `/3d`       - Location for printable 3d files like stl, obj etc.
  - `thingdata.json`  - Storage for Thing metadata / settings

## thingdata.json

Example `thingdata.json`, providing Thing metadata:

```json
{
    "id": 1234567,
    "name": "BestThing",
    "creator": "Chrismettal",
    "is_wip": true,
    "license": "gpl",
    "category": "3D Printer Parts",
    "tags": [
        "3D",
        "Printing"
    ],
    "is_published": false
}
```

## Supported files

Supported file extensions are practically arbitrary for Thingideploy and might later be read in from a seperate file rather than being hardcoded. Only there as a sanity check so you don't try uploading executables to Thingiverse.

### Model files:

- .stl
- .stp
- .STEP
- .obj
- .3mf
- .gcode

### Source files:

- .FCStd
- .scad
- .f3d

### Image files:

- .png
- .jpg
- .bmp