#!/usr/bin/python
import argparse
import json
import os
import requests
import webbrowser
from rauth import OAuth2Service


def main():
    ##########################################################################
    ##                            Arguments                                 ##
    ##########################################################################

    # path
    parser = argparse.ArgumentParser(description='Upload 3D printing project to Thingiverse automatically')
    parser.add_argument('path', metavar='path', type=str,
                        help='Path to expected folder structure')                  
    parser.add_argument('clientid', metavar='clientid', type=str, 
                        help='Thingiverse client id')
    parser.add_argument('secret', metavar='secret', type=str, 
                        help='Thingiverse client secret')
    parser.add_argument('newtoken', metavar='newtoken', type=str, 
                        help='New Thingiverse token')
    args = parser.parse_args()
    
    # generate error if no path provided, no sanity check on type of path argument yet
    if not os.path.isdir(args.path):
        print('The path specified does not exist')
        exit()

    projectpath     = args.path
    client_id       = args.clientid
    client_secret   = args.secret
    new_token       = args.newtoken

    ##########################################################################
    ##                               Init                                   ##
    ##########################################################################

    # new token has read and write acces, only created manually with URL popup, using client_id and client_secret
    headers = {'Authorization': 'Bearer ' + new_token}

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
        #print("Description: ")
        #print(desc)
        #print()

    # Tags
    tagpath = projectpath + "/tags.md"
    with open(tagpath, "r", encoding="utf-8") as f:
        tags = f.read()
        #print("Tags: ")
        #print(tags)
        #print()

    # Flags
    flagpath = projectpath + "/flags.json"
    with open(flagpath, "r", encoding="utf-8") as f:
        flags = json.load(f)
        #print("Flags: ")
        #print(flags)
        #print()

        # check if thing already exists, if thingid is provided
        if flags['thingid'] != '':
            mode = "patch"
            thing = json.loads(requests.get('http://api.thingiverse.com/things/' + str(flags['thingid']), headers=headers).text)
            if thing["id"] == flags["thingid"]:
                print("Thing already exists, running in patch mode")
            else:
                print("Thing ID specified in flags.json but thing doesn't exist or name doesn't match, aborting")
                exit()
        else:
            mode = "create"
            print('Thing does not exist yet, running in creation mode')
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

    #print("Found 3D files: ")
    #for file in threedfiles:
    #    print(file)
    #print()

    # Gcodes
    gcodepath = projectpath + "/gcode"
    gcodefiles = []
    for file in os.listdir(gcodepath):
        if (file.endswith(".gcode")):
            gcodefiles.append(os.path.join(gcodepath, file))

    #print("Found gcode files: ")
    #for file in gcodefiles:
    #    print(file)
    #print()

    # Images
    imgpath = projectpath + "/img"
    imgfiles = []
    for file in os.listdir(imgpath):
        if (file.endswith(".png")  or
            file.endswith(".jpg")  or
            file.endswith(".bmp")):
            imgfiles.append(os.path.join(imgpath, file))

    #print("Found image files: ")
    #for file in imgfiles:
    #    print(file)
    #print()


    ##########################################################################
    ##                     Thingiverse deployment                           ##
    ##########################################################################
    #headers = {'Authorization': 'Bearer ' + auth_token}
    #thing = json.loads(requests.get('http://api.thingiverse.com/things/4395209', headers=headers).text)
    #print(thing["name"])

    if mode == "create":
        print("Creating thing")

        # paste in some stuff and hope it werks, getting a new authorized token or something
        #Authservice = OAuth2Service(
        #    name='thingiverse',
        #    client_id=client_id,
        #    client_secret=client_secret,
        #    access_token_url='https://www.thingiverse.com/login/oauth/access_token',
        #    authorize_url='https://www.thingiverse.com/login/oauth/authorize',
        #    base_url='https://api.thingiverse.com')
        ## let's get the url to go to
        #authparams = {'redirect_uri': 'https://www.thingiverse.com',
        #              'response_type': 'token'}
        #url = Authservice.get_authorize_url(**authparams)
        #webbrowser.open_new(url)
        #access_code = raw_input("access token: >")

        # initial file creation
        params = {'name': flags["thingname"], 'license': flags["license"], 'category': flags["category"]}
        thing = json.loads(requests.post('http://api.thingiverse.com/things/', headers=headers, data=json.dumps(params)).text)
        NewThingId = thing["id"]
        if NewThingId != '':
            print("Thing created succesful, Thing ID:")
            print(NewThingId)
        
        # Update flags document with newly created ID
        flags["thingid"] = NewThingId
        with open(flagpath, "w", encoding="utf-8") as f:
            f.write(json.dumps(flags))

    elif mode == "patch":
        print("Patching thing")


    # Uploads need to be done the same, no matter if creating or patching mode is active
    
    params = {"is_wip": True, "description": "I made this on the web"}
    response = requests.patch('http://api.thingiverse.com/things/' + str(flags["thingid"]) + "/", headers=headers, data=json.dumps(params))
    print(json.dumps(params))
    print(response.text)
    
    #print("Asking: " + 'http://api.thingiverse.com/things/' + str(flags["thingid"]) + "/")
    #response = requests.get('http://api.thingiverse.com/things/' + str(flags["thingid"]) + "/", headers=headers)
    #print(response.text)

##########################################################################
##                        main() idiom                                  ##
##########################################################################
if __name__ == '__main__':
    main()