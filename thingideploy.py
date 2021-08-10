#!/usr/bin/python
import argparse
import json
import sys
import os
import requests
import webbrowser
import time
from datetime import datetime, timezone
from rauth import OAuth2Service

def request_token(client_id):
    """Take app client ID and generate an API token with write acces"""
    print("Requesting token is not implemented yet")

    # paste in some stuff and hope it werks, getting a new authorized token or something
    #Authservice = OAuth2Service(
    #    name="thingiverse",
    #    client_id=client_id,
    #    client_secret=client_secret,
    #    access_token_url="https://www.thingiverse.com/login/oauth/access_token",
    #    authorize_url="https://www.thingiverse.com/login/oauth/authorize",
    #    base_url="https://api.thingiverse.com")
    ## let's get the url to go to
    #authparams = {"redirect_uri": "https://www.thingiverse.com",
    #              "response_type": "token"}
    #url = Authservice.get_authorize_url(**authparams)
    #webbrowser.open_new(url)
    #access_code = raw_input("access token: >")


def create_initial_folder_structure(project_path):
    """Create the initial project structure at the target location"""
    print("Creating initial project structure is not implemented yet")


def deploy_files(access_path, files, whitelist, thingdata, headers):
    ########## File checks

    existing_files = json.loads(
                        requests.get("http://api.thingiverse.com/things/"
                            + str(thingdata["id"])
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

                elif access_path == "/images":
                    print("Replacing existing image: " + localfile["name"])
                    files_to_patch.append(remotefile)
                    files_to_delete.append(remotefile)
                    files_to_upload.append(localfile)
                print()
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

    print()

    ########## File deletions

    for file in files_to_delete:

        print("Starting deletion of " + file["name"])

        deletion_response = json.loads(
                          requests.delete(
                              "http://api.thingiverse.com/things/"
                                + str(thingdata["id"])
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
                                        + str(thingdata["id"])
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


def deploy_project(project_path, api_token):
    """Deploy the project using an API token generated by --request-token"""

    print("Deploying project")

    ##########################################################################
    ##                              Init                                    ##
    ##########################################################################

    headers = {"Authorization": "Bearer " + api_token}

    ##########################################################################
    ##                          File parsing                                ##
    ##########################################################################

    # Thing data
    datapath = project_path + "/thingdata.json"
    with open(datapath, "r", encoding="utf-8") as f:
        thingdata = json.load(f)
        #print("Thingdata: ")
        #print(thingdata)
        #print()

        # check if thing already exists, if id is provided
        if thingdata["id"] != "":
            thing = json.loads(
                        requests.get("http://api.thingiverse.com/things/" 
                                    + str(thingdata["id"]), 
                                    headers=headers).text)

            # compare provided name with found creator name as sanity check
            if thingdata["creator"] == thing["creator"]["name"]:
                mode = "patch"
                print("Thing already exists, running in patch mode")
            else:
                print("""Thing ID specified in flags.json does not belong to 
                         creator, exiting""")
                sys.exit(os.EX_NOPERM)

        else:
            mode = "create"
            print("No thing ID provided, running in creation mode")
        print()

    # Description
    descpath = project_path + "/README.md"
    with open(descpath, "r", encoding="utf-8") as f:
        description = f.read()
        print("--------------Description---------------")
        print(description)
        print("----------------------------------------")

    # model / source files
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
    print()

    # Images
    imgpath         = project_path + "/img"
    imgfiles        = []
    for file in os.listdir(imgpath):
        if (file.endswith(".png") or
            file.endswith(".jpg") or
            file.endswith(".bmp")):
            imgfiles.append({"name":file, 
                             "path":os.path.join(imgpath, file)})

    print("Found image files: ")
    for file in imgfiles:
        print(file["name"])
    print()


    ##########################################################################
    ##                     Thingiverse deployment                           ##
    ##########################################################################
    
    ########## Thing creation
    # If ID wasn't already found, first create thing
    if mode == "create":

        print("Creating thing")

        # initial file creation
        params = {"name":           thingdata["name"],
                  "license":        thingdata["license"],
                  "category":       thingdata["category"],
                  "description":    description,
                  "instructions":   "None provided",
                  "is_wip":         thingdata["is_wip"],
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
        thingdata["id"] = new_thing_id
        with open(datapath, "w", encoding="utf-8") as f:
            f.write(json.dumps(thingdata, indent=4))


    ########## Thing info patching  
    # Otherwise, go into patching mode
    elif mode == "patch":
        
        print("Patching thing")


        params = {"name":           thingdata["name"],
                  "license":        thingdata["license"],
                  "category":       thingdata["category"],
                  "description":    description,
                  "instructions":   "None provided",
                  "is_wip":         thingdata["is_wip"],
                  "tags":           thingdata["tags"]}
        patch = requests.patch("http://api.thingiverse.com/things/"
                                    + str(thingdata["id"])
                                    + "/", headers=headers,
                                    data=json.dumps(params))

        # wait a tick before pulling an answer
        # since Thingiverse does not populate all answers instantly
        print("Waiting for Thingiverse to refresh tags in response")
        time.sleep(2) 

        patch = json.loads(requests.get("http://api.thingiverse.com/things/"
                                    + str(thingdata["id"])
                                    + "/", headers=headers).text)

        # Output response to file for debugging, loads/dumps formats document
        with open(project_path + "/PatchResponse.json", "w") as f:
                f.write(json.dumps(patch, indent=4))

        # check if valid answer received
        if patch["id"] == thingdata["id"]:
            print("Thing patching succesful")
    
    print("Deploying model files:")
    deploy_files("/files", modelfiles, "whitelist", thingdata, headers)

    print("Deploying images:")
    deploy_files("/images", imgfiles, modelfiles, thingdata, headers)


def main():
    ##########################################################################
    ##                              Intro                                   ##
    ##########################################################################

    print()
    print("----------------------------------------")
    print("---------- Thingideploy start ----------")
    print("----------------------------------------")
    print()


    ##########################################################################
    ##                            Arguments                                 ##
    ##########################################################################

    parser = argparse.ArgumentParser(description=
                     "Upload 3D printing project to Thingiverse automatically")

    # required path
    parser.add_argument("path", metavar="path", type=str,
                        help="Path to project structure")

    # optional flag to create project structure at path
    parser.add_argument("--create-project",
                         action="store_true",
                        help="Create project structure if set")

    # optional clientid input whith which a token is requested
    parser.add_argument("--request-token", metavar="clientid", type=str, 
                        help="If set creates token with supplied client ID")

    # hopefully not needed anymore
    #parser.add_argument("secret", metavar="secret", type=str, 
    #                    help="Thingiverse client secret")

    # optional token which is used for actual write access
    parser.add_argument("--deploy-project", metavar="apitoken", type=str, 
                        help="API token generated by using --create-token")
    args = parser.parse_args()


    # generate error if no path provided 
    if not os.path.isdir(args.path):
        print("The path specified does not exist, exiting")
        sys.exit(os.EX_USAGE)

    project_path    = args.path
    client_id       = str(args.request_token)
   #client_secret   = args.secret   # seems to not be needed
    api_token       = str(args.deploy_project)

    # prioritize between different modes
    if args.create_project:
        create_initial_folder_structure(project_path)

    elif args.request_token:
        request_token(client_id)

    elif args.deploy_project:
        deploy_project(project_path, api_token)
    else:
        print("No mode chosen (create / patch), exiting")
        sys.exit(os.EX_USAGE)

    # exit with exit code 0
    sys.exit(os.EX_OK)

##########################################################################
##                        main() idiom                                  ##
##########################################################################
if __name__ == "__main__":
    main()