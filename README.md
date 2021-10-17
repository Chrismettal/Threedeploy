![Banner](img/Banner.png)

[![GitLab tag (latest by SemVer)](https://img.shields.io/gitlab/v/tag/chrismettal/threedeploy?label=Master&style=flat-square)](https://gitlab.com/Chrismettal/threedeploy/-/tags)
[![PyPI - Version](https://img.shields.io/pypi/v/threedeploy?style=flat-square)](https://pypi.org/project/threedeploy/)
[![PyPI - License](https://img.shields.io/pypi/l/threedeploy?style=flat-square)](https://pypi.org/project/threedeploy/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/threedeploy?style=flat-square)](https://pypi.org/project/threedeploy/)

Python app to automatically deploy a project to Thingiverse. Can be used manually, but is really supposed to be used via GitLab CI/CD or Github Actions for example.

Providing the correct project structure, Thingideploy will do the following:
- Read Thing metadata from `thingdata.json`
- Create a Thing based on your provided data, or patch an existing one
- Update the name, tags, ~~description~~ (currently broken on Thingi side apparently), license, category and WIP state of your thing
- Publish your thing, if flag is set
- Upload found 3D files / known project source files, or replace existing ones if local files have been modified since upload
- Upload found images or replace existing ones

Additionaly, there is a [project creation mode](#project-creation-mode) to create the [expected folder structure](#expected-folder-structure) and generate initial Thing metadata, as well as an [API token request mode](#api-token-request-mode) to generate your own API token.

Please see my [example Repo](https://gitlab.com/chrismettal/LasS0) where Thingideploy is used for automatic CI/CD deployment!

![ExampleScreenshot](img/Thingiverse-Example.png)


If you like my work please consider supporting my caffeine addiction!

<a href='https://ko-fi.com/U7U6G0X3' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://az743702.vo.msecnd.net/cdn/kofi4.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

---

:construction: :construction: :construction:

### WIP WARNING <!-- omit in toc -->

This is a WIP. While all functions except updating Thing summary work, there is little in the way of error handling or sanity checking of data.

:construction: :construction: :construction:

---

# Table of contents <!-- omit in toc -->

- [Usage](#usage)
  - [Requirements](#requirements)
  - [Project creation mode](#project-creation-mode)
  - [Thingiverse API token request mode](#thingiverse-api-token-request-mode)
  - [Deployment mode - Thingiverse](#deployment-mode---thingiverse)
  - [Pipeline usage](#pipeline-usage)
- [Expected folder structure](#expected-folder-structure)
- [thingdata.json](#thingdatajson)
- [Supported files](#supported-files)
  - [Model files:](#model-files)
  - [Source files:](#source-files)
  - [Image files:](#image-files)


# Usage


## Requirements

With Python 3 and PIP installed run:

`pip install --upgrade threedeploy`

## Project creation mode 

```bash
threedeploy --create-project --path=</path/to/new/project_folder>
```

Will create the [expected project structure](#expected-folder-structure) along with all required files at the given location, inside `project_folder`. 

*Warning*, `project_folder` itself needs to exist before calling, as the other modes could break if it doesn't already.

Every text file that already exists, will be backed up like `thingdata.json` --> `thingdata.json.backup_<Timestamp>` before the new file is generated fresh. These backup files are put in the `.gitignore` so make sure to not `git clean` them away when overwriting your files accidentaly.


## Thingiverse API token request mode

```bash
threedeploy --request-token-thingiverse
```

Will open up your default webbrowser, promting you to login to Thingiverse and grant access to Thingideploy. 

After you have granted access, you will be forwarded to the Thingiverse homepage, but the response URL in your browsers address bar will contain your newly created API token. Copy this whole link and paste it into the command line when promted. Thingideploy will sanity check the link provided, and show you your API key for safekeeping. 

The API key is NOT saved in the application in any form and is only shown shown now! Save the key in a safe location, and use it later in deployment mode with the argument `--deploy-project <YourApiToken`.

*Warning*, Thingideploy is currently in Thingiverses submission queue. Until it is approved by Thingiverse, only 10 people can use my applications client ID to use Thingideploy! Should that happen before Thingiverse approved Thingideploy, I will add instructions on how to create your own Thingiverse application to generate your own client ID so you can request an API token.


## Deployment mode - Thingiverse

```bash
threedeploy --deploy-project-thingiverse=<YourApiToken> --path=</path/to/new/project_folder>
```

Will deploy your project to Thingiverse. The first time this is called, a new Thing is created on Thingiverse, `thingdata.json` will be updated with the new `thing_id`, and all your files will be uploaded for the first time. If the Thing already exists (checked with `thingdata.json`.`thing_id`) it will try to patch your Thing. 

*Warning*, If you run Thingideploy in a CI/CD pipeline, it will not be able to easily update your repos `thingdata.json`. It IS possible to give CI/CD runners push access, but since it will only need it once for initial deployment it is not really worth it. You will manually need to update `thingdata.json` with the new ThingID that is output to the command line and artifacted as `ThingId.txt` on successful creation!

Please also check [Pipeline usage](#pipeline-usage) for information on how to automate deployment.

Deploying your thing will:

- Compare model / gcode and source files on Thingiverse with your local ones, deleting and reuploading the ones where your local timestamp is newer than the upload timestamp on Thingiverse
- Delete and reupload all pictures, as there is no image timestamp to compare to
- Set display order of your images base on the [filename](#image-files)
- ~~Replace Thing summary with your README.md contents~~ / *CURRENTLY BROKEN IN API*
- Replace all tags on Thingiverse with `thingdata.json`.`tags`
- If `thingdata.json`.`is_published` is set, but thing is not already public, publish the Thing
- Add `Work in progress` information, depending on `thingdata.json`.`is_wip`
- Set `License` and `Category` depending on `thingdata.json`

*Warning*,  Thingiverse is amazingly slow to react to new file uploads and metadata changes. After calling with `--deploy-project`, allow Thingiverse to catch up for around 15 minutes before checking your Thing.


## Pipeline usage


For clarity, please see my [example Repo](https://gitlab.com/chrismettal/LasS0) where Threedeploy is used for automatic CI/CD deployment!

*Warning*, If you run Threedeploy in a CI/CD pipeline, it will not be able to easily update your repos `thingdata.json`. It IS possible to give CI/CD runners push access, but since it will only need it once for initial deployment at Thingiverse for example it is not really worth it. You will manually need to update `thingdata.json` with the new ThingID that is output to the command line and artifacted as `ThingId.txt` on successful creation!

Below is an example `.gitlab-ci.yml` to automatically deploy and update things that are tracked in a git repo. You will need to put your [Thingiverse API key](#api-token-request-mode) as a GitLab secret called `THINGIVERSE_API_KEY` to grant the runner access to Thingiverse.


```yml
stages:
  - deploy

deploy_thingiverse:
  stage: deploy
  image: "python:3.9.6-buster"
  script:
    - pip install threedeploy
    - threedeploy --deploy-project-thingiverse="$THINGIVERSE_API_KEY" --path="$CI_PROJECT_DIR"/ProjectPath/
  artifacts:
    paths:
      - $CI_PROJECT_DIR/ProjectPath/CreationResponse.json
      - $CI_PROJECT_DIR/ProjectPath/PatchResponse.json
      - $CI_PROJECT_DIR/ProjectPath/ThingURL.txt
      - $CI_PROJECT_DIR/ProjectPath/ThingID.txt
    expire_in: 1 week
  only:
    changes:
      - ProjectPath/**/*
      - ProjectPath/*
```

The runner will just install and run Threedeploy like you would on your local machine. Thingiverse responses are artifacted and the ThingURL and ThingID output just in case. Additionally, the job only triggers on changes in your 3d project path.


# Expected folder structure

The program expects files in the following structure:

- `/project_folder/`     - Path that is input as command line argument like `./thingideploy.py /home/user/project_folder`
  - `gcode/`            - Location for sliced gcode files
    - `README.md`       - Describing your gcode location
  - `img/`              - Location for images
    - `README.md`       - Describing your image location, see also [image files](#image-files)
  - `source/`           - Location for project source file, FreeCAD, OpenSCAD project file etc.
    - `README.md`       - Describing your source file location
  - `3d/`               - Location for printable 3d files like stl, obj etc.
    - `README.md`       - Describing your 3d model file location
  - `thingdata.json`    - Storage for Thing metadata / settings
  - `README.md`         - Project description that is uploaded to Thingiverse as `Summary` once the API actually works again
  - `.gitignore`        - .gitignore containing ignored files created from this script

Additionally, the script will sometimes create the following files:

- `project_folder/`
  - `**/*.backup_<Timestamp>` - When a new textfile is being created which already exists, the old one will be backed up here
  - `CreationResponse.json`   - Dump of the API response during first project deployment
  - `PatchResponse.json`      - Dump of the API response during project patching
  - `InitialCreation`         - Will get touched after initial creation, only to notify CI/CD pipelines to update `thingdata.json` with the newly received `thing_id`


# thingdata.json

Example `thingdata.json`, providing Thing metadata:

```json
{
    "name": "Threedeploy - Debug",
    "tags": [
        "NewTag",
        "SecondTag"
    ],
    "thingiverse_id": 4932869,
    "thingiverse_creator": "Chrismettal",
    "thingiverse_is_wip": true,
    "thingiverse_license": "cc",
    "thingiverse_category": "3D Printer Parts",
    "thingiverse_is_published": true
}
```

This file is required to exist before deployment, and is best generated with the `--create-project` option.

`thingiverse_creator` is just used as a plausibility check before trying to patch a Thing that you don't own, so it needs to contain your Thingiverse name.All other options have direct impact on all Thing settings that are exposed to the API. Thing summary is supposed to be set via the projects `project_path/README.md` but currently does not work.


# Supported files

Supported file extensions are practically arbitrary for Thingideploy and might later be read in from a seperate file rather than being hardcoded. Only there as a sanity check so you don't try uploading executables to Thingiverse.


## Model files:

- .stl
- .stp
- .STEP
- .obj
- .3mf
- .gcode


## Source files:

- .FCStd
- .scad
- .f3d


## Image files:

- .png
- .jpg
- .bmp

Image files are sorted (ranked) via the file name. Make sure to use the following naming format:

`RR-YourImageName.*`

Where `RR` is a 2 char integer for image ranking, for example `01-Cover.png` will put your that file as the first image in order. Make sure every image has a unique rank name, like:

- `01-Cover.png`
- `02-Side.png`
- ...
- `12-FinalPicture.png`
