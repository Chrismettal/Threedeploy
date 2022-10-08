#!/usr/bin/python
import argparse
import json
import sys
import os
import requests
import webbrowser
import time
import re
from datetime import datetime, timezone
from shutil import copyfile

##########################################################################
##                          Global constants                            ##
##########################################################################
# The Thingiverse ID of this app for requesting an API key
THINGIVERSE_CLIENT_ID = "844fde0b2950ccf35329"  

##########################################################################
##                            Helpers                                   ##
##########################################################################

########## General
def create_textfile(path, data):
    """Creates a new textfile, backing up already existing files if found"""
    # Backup file if it already exists
    if os.path.isfile(path):
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S")
        copyfile(path, path + ".backup_" + timestamp)

    # Create or overwrite original file
    with open(path, "w") as f:
                f.write(data)

########## Thingiverse
def thingiverse_deploy_files(access_path, files, whitelist, thingdata, headers):
    """Deploys files.."""

    ########## File checks

    existing_files = json.loads(
                        requests.get("http://api.thingiverse.com/things/"
                            + str(thingdata["thingiverse_id"])
                            + access_path, headers=headers).text)


    # check for upload vs patch
    files_to_upload = []
    files_to_patch  = []
    files_to_delete = []

    for localfile in files:
        upload_required = True
        for remotefile in existing_files:
            # If a matching file is found on remote, append it onto patch list.
            # This will include id etc.
            if remotefile["name"] == localfile["name"]:
                upload_required = False

                # Only check timestamps for file types, not images
                if access_path == "/files":
                    # The timestamp from strptime is naive and assumes my
                    # timezone, which I need to strip in a second step
                    naive_upload_timestamp = datetime.strptime(
                                                remotefile["date"],
                                                "%Y-%m-%d %H:%M:%S")

                    upload_timestamp =  datetime.timestamp(
                                          naive_upload_timestamp.replace(
                                              tzinfo=timezone.utc))

                    print("Checking timestamps for existing file:")
                    print(remotefile["name"])
                    if localfile["date"] > upload_timestamp:
                        print("Replacing file")
                        files_to_patch.append(remotefile)
                        files_to_delete.append(remotefile)
                        files_to_upload.append(localfile)
                    else:
                        print("Keeping uploaded version")

                # Replacing images is not enabled anymore.
                #elif access_path == "/images":
                #    print("Replacing existing image: " + localfile["name"])
                #    files_to_patch.append(remotefile)
                #    files_to_delete.append(remotefile)
                #    files_to_upload.append(localfile)
                break
        if upload_required:
            files_to_upload.append(localfile)


    # check for files to delete
    for remotefile in existing_files:
        deletion_required = True

        for localfile in files:
            # if a matching file is found locally, don't delete it.
            if (remotefile["name"] == localfile["name"]):
                deletion_required = False
                break

        if access_path == "/images":
            for whitelistfile in whitelist:
                # also keep auto generated images by thingiverse, which is 
                # always "<NameOfExisting3dFile>.png", pulled from whitelist
                if (remotefile["name"] == os.path.splitext(
                                            whitelistfile["name"])[0] 
                                            + ".png"):
                    deletion_required = False
                    break

        if deletion_required:
            files_to_delete.append(remotefile)


    # output upcoming file operations
    print("Files to be uploaded:")
    for file in files_to_upload:
        print(file["name"])

    print("Files to be deleted:")
    for file in files_to_delete:
        print(file["name"])

    ########## File deletions

    for file in files_to_delete:

        print("Starting deletion of " + file["name"])

        deletion_response = json.loads(
                          requests.delete(
                              "http://api.thingiverse.com/things/"
                                + str(thingdata["thingiverse_id"])
                                + access_path + "/"
                                + str(file["id"]),
                                headers=headers).text)

        #print(json.dumps(deletion_response, indent=4))

    ########## File uploads

    for file in files_to_upload:
        print("Starting upload of " + file["name"])

        # open up transfer
        print("Opening transfer")
        params = {"filename":file["name"]}
        upload_creds = json.loads(
                        requests.post("http://api.thingiverse.com/things/"
                                        + str(thingdata["thingiverse_id"])
                                        + "/files",
                                        data=json.dumps(params),
                                        headers=headers).text)
        #print(json.dumps(upload_creds, indent=4))

        # actually transfer
        print("Starting transfer")

        files = {'file': open(file["path"], 'rb')}
        params = upload_creds["fields"]

        requests.post(
            "http://thingiverse-production-new.s3.amazonaws.com",
            files=files, data=params, 
            allow_redirects=False).text

        # close transfer
        print("Closing transfer")
        finalize_response = json.loads(
                             requests.post(
                              upload_creds["fields"]["success_action_redirect"],
                              headers=headers).text)


def thingiverse_set_image_order(imgfiles, thingdata, headers):
    """Sets image order of recently uploaded pictures, based on filename"""

    print("Ranking images based on file names")

    existing_images = json.loads(
                        requests.get("http://api.thingiverse.com/things/"
                            + str(thingdata["thingiverse_id"])
                            + "/images", headers=headers).text)

    # Iterate through uploaded files
    number_of_invalid_filenames = 0
    for remote_image in existing_images:
        # Assign rank to each file that has a valid name
        if re.match("[0-9][0-9]-+", remote_image["name"]) is not None:
            remote_image["rank"] = remote_image["name"][:2]
            print("Found valid filename: " +
                    remote_image["name"] + 
                    ", Rank: ",
                    remote_image["rank"])
        # If no valid name is found, assign rank starting from 100
        else:
            remote_image["rank"] = 100 + number_of_invalid_filenames
            number_of_invalid_filenames += 1

            print("Not a valid filename for ranking: " + 
                    remote_image["name"] + 
                    ", Rank: ",
                    remote_image["rank"])

        # Actually patch image with new rank
        params      = {"rank":remote_image["rank"]}
        img_answer2 = requests.patch("http://api.thingiverse.com/things/" +
                                    str(thingdata["thingiverse_id"]) +
                                    "/images/"+
                                    str(remote_image["id"]),
                                    headers=headers,
                                    data=json.dumps(params))

    print("All images ranked")


def thingiverse_publish_project(thingdata, headers):
    """Create publish request"""
    # POST /things/{$id}/publish
    PublishAnswer = requests.post("http://api.thingiverse.com/things/"+
                                str(thingdata["thingiverse_id"])+
                                "/publish",
                                headers=headers)
    
    print("Thing published")


##########################################################################
##                       Token request mode                             ##
##########################################################################
########## Thingiverse
def thingiverse_request_token():
    """Take app client ID and generate an API token with write acces"""

    print("Running in API token request mode")

    # Open up a webbrowser with the authorization URL
    webbrowser.open(url = 
        "https://www.thingiverse.com/login/oauth/authorize?client_id="
        + THINGIVERSE_CLIENT_ID
        + "&response_type=token",
        new=1,
        autoraise=True);


    print("Opening webbrowser, please authorize.")
    print("After authorizing, copy the response URL")
    print("from your address bar and paste here:")
    access_code = input("Response URL: ")

    if "access_token=" not in access_code: 
        print("Invalid response URL, string \"acces_token=\" not found.")
        sys.exit(os.EX_USAGE)
    else:
        split_code = access_code.split("access_token=")

        if len(split_code[1]) > 0:
            new_api_key = split_code[1]

            print()
            print("Your API key was generated, put it in a safe location")
            print("and use it for deploying like --deploy-project=<ApiKey>")
            print()
            print("Key: ")
            print(new_api_key)
            print()
            print("Using this, you can run '--deploy-project-thingiverse <API_KEY>'!")
        else:
            print("Invalid response URL, api token empty.")
            sys.exit(os.EX_USAGE)

##########################################################################
##                  Initial project creation mode                       ##
##########################################################################
def create_initial_folder_structure(project_path):
    """Create the initial project structure at the target location"""

    print("Creating initial project structure at:")
    print(project_path)

    # Create overall project README
    create_textfile(path = project_path + "/README.md",
                    data =
    "# Project Name\n\n"
    "Summary of your project.\n\n"
    "Published with [Threedeploy]"
    "(https://gitlab.com/chrismettal/threedeploy)\n"
    )

    # Create .gitignore
    create_textfile(path = project_path + "/.gitignore",
                    data = 
    "# Threedeploy specific\n\n"
    "CreationResponse.json\n"
    "PatchResponse.json\n"
    "*.backup_*\n"
    "InitialCreation\n"
    "ThingURL.txt\n"
    "ThingID.txt\n"
    "ApiToken.txt\n"
    )

    # Create initial thingdata.json
    thingdata = {
                "name"                      :"Threedeploy Project Name",
                "tags"                      : [
                                            "YourTagsHere",
                                            "likeThis"
                                            "Threedeploy",
                ],
                "thingiverse_id"            :"",
                "thingiverse_creator"       :"YourThingiverseNameHere",
                "thingiverse_is_wip"        :True,
                "thingiverse_license"       :"gpl",
                "thingiverse_category"      :"3D Printing",
                "thingiverse_is_published"  :False
    }
    create_textfile(path = project_path + "/thingdata.json",
                    data =json.dumps(thingdata, indent=4))

    # Create folders
    if not os.path.exists(project_path + "/3d"):
        os.mkdir(project_path + "/3d")
    if not os.path.exists(project_path + "/gcode"):
        os.mkdir(project_path + "/gcode")
    if not os.path.exists(project_path + "/img"):
        os.mkdir(project_path + "/img")
    if not os.path.exists(project_path + "/source"):
        os.mkdir(project_path + "/source")

    # Put readmes in folders for git tracking
    create_textfile(path = project_path + "/3d/README.md",
                    data =
    "# 3D file location\n\n"
    "Put your model files here, for example .stl, .STEP, .obj etc.\n"
    )

    create_textfile(path = project_path + "/gcode/README.md",
                    data =
    "# Gcode location\n\n"
    "Put your sliced gcodes here\n"
    )

    create_textfile(path = project_path + "/img/README.md",
                    data =
    "# Image location\n\n"
    "Put your images here\n\n"
    "Image files are sorted (ranked) via the file name. "
    "Make sure to use the following naming format:\n\n"
    "`RR-YourImageName.*`\n\n"
    "Where `RR` is a 2 char integer for image ranking, "
    "for example `01-Cover.png` will put your that file "
    "as the first image in order.\n"
    )

    create_textfile(path = project_path + "/source/README.md",
                    data =
    "# Source file location\n\n"
    "Put your source files here, for example .FCStd, .scad etc.\n"
    )

    print("Success!")


##########################################################################
##                     Project deployment mode                          ##
##########################################################################

########## General
def deploy_project(project_path, api_token, destination):
    """Deploy the project using an API token generated by --request-token"""

    print("Deploying project:")

    ##########################################################################
    ##                          File parsing                                ##
    ##########################################################################

    ########## Thing data
    datapath = project_path + "/thingdata.json"
    if not os.path.isfile(datapath):
        print("thingdata.json does not exist, have you created your project?")
        sys.exit(os.EX_USAGE)

    with open(datapath, "r", encoding="utf-8") as f:
        thingdata = json.load(f)

    print(thingdata["name"])

    ########## Description
    descpath = project_path + "/README.md"
    with open(descpath, "r", encoding="utf-8") as f:
        description = f.read()
        print("--------------Description---------------")
        print(description)
        print("----------------------------------------")

    ########## model / source files
    threedpath      = project_path + "/3d"
    sourcepath      = project_path + "/source"
    gcodepath       = project_path + "/gcode"
    modelfiles      = []
    for file in os.listdir(threedpath):
        if (file.endswith(".stl")  or
            file.endswith(".obj")  or
            file.endswith(".stp")  or
            file.endswith(".STEP") or
            file.endswith(".3mf")):
            modelfiles.append({"name":file, 
                                "path":os.path.join(threedpath, file),
                                "date":os.path.getmtime(
                                    os.path.join(threedpath, file))})

    for file in os.listdir(sourcepath):
        if (file.endswith(".FCStd")  or
            file.endswith(".scad")  or
            file.endswith(".f3d")):
            modelfiles.append({"name":file, 
                                "path":os.path.join(sourcepath, file),
                                "date":os.path.getmtime(
                                    os.path.join(sourcepath, file))})

    for file in os.listdir(gcodepath):
        if file.endswith(".gcode"):
            modelfiles.append({"name":file, 
                                "path":os.path.join(gcodepath, file),
                                "date":os.path.getmtime(
                                    os.path.join(gcodepath, file))})

    print("Found model files: ")
    for file in modelfiles:
        print(file["name"])
    print("----------------------------------------")

    ########## Images
    imgpath         = project_path + "/img"
    imgfiles        = []
    for file in os.listdir(imgpath):
        if (file.endswith(".png") or
            file.endswith(".jpg") or
            file.endswith(".bmp")):
            imgfiles.append({"name":file, 
                             "path":os.path.join(imgpath, file),
                             "thingiverse_id":0})

    print("Found image files: ")
    for file in imgfiles:
        print(file["name"])
    print("----------------------------------------")

    ##########################################################################
    ##                    Site specific deployment                          ##
    ##########################################################################
    if destination == 'thingiverse':
        print("Deploying to Thingiverse!")
        deploy_thingiverse(api_token, thingdata, project_path, modelfiles, imgfiles)

    elif destination == 'myminifactory':
        print('MyMiniFactory deployment not implemented yet, sorry')
        sys.exit(OS.EX_USAGE)

    elif destination == 'prusaprinters':
        print('PrusaPrinters deployment not implemented yet, sorry')
        sys.exit(OS.EX_USAGE)

    elif destination == 'thangs':
        print('Thangs deployment not implemented yet, sorry')
        sys.exit(OS.EX_USAGE)

########## Thingiverse
def deploy_thingiverse(api_token, thingdata, project_path, modelfiles, imgfiles):
    ##########################################################################
    ##                     Thingiverse deployment                           ##
    ##########################################################################
    ########## Thing data
    datapath = project_path + "/thingdata.json"
    
    headers = {"Authorization": "Bearer " + api_token}
    
    # check if thing already exists, if id is provided
    if thingdata["thingiverse_id"] != "":
        thing = json.loads(
                    requests.get("http://api.thingiverse.com/things/" 
                                + str(thingdata["thingiverse_id"]), 
                                headers=headers).text)

        # Check if we returned an error
        if "error" in thing:
            if thing["error"] == "Unauthorized":
                print("Unauthorized, is your API key correct? Exiting")
                sys.exit(os.EX_NOPERM)
            if thing["error"] == "Not Found":
                print("Thing ID specified but Thing not found, exiting")
                sys.exit(os.EX_USAGE)

        # compare provided name with found creator name as sanity check
        if thingdata["thingiverse_creator"] == thing["creator"]["name"]:
            mode = "patch"
            print("Thing already exists, running in patch mode")
        else:
            print("""Thing ID specified in thingdata.json does not belong to 
                        creator, exiting""")
            sys.exit(os.EX_NOPERM)

    else:
        mode = "create"
        print("No thing ID provided, running in creation mode")
    print("----------------------------------------")

    ########## Thing creation
    # If ID wasn't already found, first create thing
    if mode == "create":

        print()
        print("Creating thing")

        # initial file creation
        params = {"name":           thingdata["name"],
                  "thingiverse_license":        thingdata["thingiverse_license"],
                  "thingiverse_category":       thingdata["thingiverse_category"],
                 #"description":    currently broken on Thingiverse,
                 #"instructions":   currently broken on Thingiverse,
                  "thingiverse_is_wip":         thingdata["thingiverse_is_wip"],
                  "tags":           thingdata["tags"]}

        thing = json.loads(
                        requests.post("http://api.thingiverse.com/things/",
                        headers=headers,
                        data=json.dumps(params)).text)

        # Output response to file for debugging
        with open(project_path + "/CreationResponse.json", "w") as f:
            f.write(json.dumps(thing, indent=4))

        new_thing_id = thing["id"]

        # check if valid answer received
        if new_thing_id != "":
            print("Thing creation succesful, thing ID:")
            print(new_thing_id)
        
        # Update flags document with newly created ID
        thingdata["thingiverse_id"] = new_thing_id
        with open(datapath, "w", encoding="utf-8") as f:
            f.write(json.dumps(thingdata, indent=4))

        # Output initial creation file for pipeline
        with open(project_path + "/InitialCreation", "w") as f:
            print("InitialCreation file generated")
            f.write("Initial creation success")


    ########## Thing info patching  
    # Otherwise, go into patching mode
    elif mode == "patch":
        
        print("Patching thing")

        params = {"name":           thingdata["name"],
                  "thingiverse_license":        thingdata["thingiverse_license"],
                  "thingiverse_category":       thingdata["thingiverse_category"],
                 #"description":    description,
                 #"instructions":   "None provided",
                  "thingiverse_is_wip":         thingdata["thingiverse_is_wip"],
                  "tags":           thingdata["tags"]}

        requests.patch("http://api.thingiverse.com/things/"
                                    + str(thingdata["thingiverse_id"])
                                    + "/", headers=headers,
                                    data=json.dumps(params))

        # wait a tick before pulling an answer
        # since Thingiverse does not populate all answers instantly
        print("Waiting for Thingiverse to refresh tags in response")
        time.sleep(2) 

        thing = json.loads(requests.get("http://api.thingiverse.com/things/"
                                    + str(thingdata["thingiverse_id"])
                                    + "/", headers=headers).text)

        already_published = thing["is_published"]

        # Output response to file for debugging, loads/dumps formats document
        with open(project_path + "/PatchResponse.json", "w") as f:
                f.write(json.dumps(thing, indent=4))

        # Check if valid answer received
        if thing["id"] == thingdata["thingiverse_id"]:
            print("Thing patching succesful")
    
        # Remove InitialCreation file on repeat runs
        if os.path.exists(project_path + "/InitialCreation"):
            os.remove(project_path + "/InitialCreation")
            print("InitialCreation file removed")


    # Model file upload
    print("----------------------------------------")
    print("Deploying model files:")
    thingiverse_deploy_files("/files", modelfiles, "whitelist", thingdata, headers)

    # Image upload
    print("----------------------------------------")
    print("Deploying images:")
    thingiverse_deploy_files("/images", imgfiles, modelfiles, thingdata, headers)
    thingiverse_set_image_order(imgfiles, thingdata, headers)

    # Publishing
    print("----------------------------------------")
    print("Testing if publishing is required")
    if thingdata["thingiverse_is_published"] and not thing["is_published"]:
        print("Publishing thing")
        thingiverse_publish_project(thingdata, headers)

    elif not thingdata["thingiverse_is_published"]:
        print("Publishing not requested")

    elif thing["is_published"]:
        print("Thing already published")


    # Output thing URL to artifact and terminal
    thing_url = "https://thingiverse.com/thing:" + str(thingdata["thingiverse_id"])
    print("----------------------------------------")
    print("Deploying done! Thing URL: ")
    print(thing_url)
    print("Thing ID:")
    print(thingdata["thingiverse_id"])
    print("----------------------------------------")

    with open(project_path + "/ThingURL.txt", "w") as f:
        f.write(thing_url)

    with open(project_path + "/ThingID.txt", "w") as f:
        f.write(str(thingdata["thingiverse_id"]))


##########################################################################
##                             main()                                   ##
##########################################################################
def main():
    
    print()
    print("----------------------------------------")
    print("----------- Threedeploy start ----------")
    print("----------------------------------------")


    ##########################################################################
    ##                            Arguments                                 ##
    ##########################################################################

    parser = argparse.ArgumentParser(description=
                     "Upload 3D projects to multiple sites automatically")

    # Project path
    parser.add_argument("--path", metavar="path", type=str,
                        help=
    "Path to project structure")

    # Create folder structure mode
    parser.add_argument("--create-project",
                         action="store_true",
                        help=
    "Create project structure if set. "
    "Will backup existing files to *.backup_TIMESTAMP"
    )

    # Request API token from Thingiverse
    parser.add_argument("--request-token-thingiverse", 
                        action="store_true",
                        help=
    "Requests API token from Thingiverse if set")


    # Deploy to Thingiverse, using the provided Thingiverse API key
    parser.add_argument("--deploy-project-thingiverse", 
                        metavar="thingiverse_apitoken",
                        type=str, 
                        help=
    "Deploy to Thingiverse if set. "
    "Input Thingiverse API token, generated with --request-token-thingiverse")

    
    args = parser.parse_args()


    ##########################################################################
    ##                              Modes                                   ##
    ##########################################################################

    ########## project creation mode
    if args.create_project:
        # Test path
        if not args.path:
            print("Please provide project path with --path <ProjectPath>")
            sys.exit(os.EX_USAGE)
        if not os.path.isdir(args.path):
            print("The path specified does not exist, exiting")
            sys.exit(os.EX_USAGE)

        create_initial_folder_structure(args.path)

    ########## thingiverse API token request
    elif args.request_token_thingiverse:
        thingiverse_request_token()

    ########## project deployment
    elif args.deploy_project_thingiverse:
        # or myminifactory
        # or prusaprinters
        # or thangs

        # Test path
        if not args.path:
            print("Please provide project path with --path <ProjectPath>")
            sys.exit(os.EX_USAGE)
        if not os.path.isdir(args.path):
            print("The path specified does not exist, exiting")
            sys.exit(os.EX_USAGE)

        # call deployment function, passing destination input
        if args.deploy_project_thingiverse:
            deploy_project(args.path, args.deploy_project_thingiverse, 'thingiverse')
        # elif myminifactory
        #    deploy_project(args.path, args.deploy-project-thingiverse, 'myminifactory')
        # elif prusaprinters
        #    deploy_project(args.path, args.deploy-project-thingiverse, 'prusaprinters')
        # elif thangs
        #    deploy_project(args.path, args.deploy-project-thingiverse, 'thangs')

    else:
        print("No mode chosen, use --help to figure out which mode you want")
        sys.exit(os.EX_USAGE)

    # exit with exit code 0
    sys.exit(os.EX_OK)


##########################################################################
##                        main() idiom                                  ##
##########################################################################
if __name__ == "__main__":
    main()
