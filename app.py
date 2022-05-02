from flask import Flask, request, abort, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
from config import XBL3_TOKEN
import dateutil.parser
import json
import requests
import time

app = Flask(__name__, static_url_path='', static_folder='static/')
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=[]
)

indexed_files = {}

with open("file_database.json") as f:
    file_database = json.load(f)
    file_database = list(sorted(file_database, key = lambda x: x["url"]))
    print("file database loaded")


def get_session(authorization_token, token_type):
    headers = {
        "User-Agent": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "Authorization": f"{token_type} {authorization_token}",
        "Ubi-AppId": "594d5ecc-0c64-441b-b129-42ceafb22c81",
        "Content-Type": "application/json"
    }
    
    if token_type == "Ubi_v1":
        headers["Authorization"] = f"{token_type} t={authorization_token}"
    
    r = requests.post("https://public-ubiservices.ubi.com/v3/profiles/sessions", headers=headers)
    
    return r.json()


def get_songdb(ubiv1_token):
    headers = {
        "User-Agent": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "Authorization": f"Ubi_v1 {ubiv1_token}",
        "X-SkuId": "jd2022-xone-all",
        "Content-Type": "application/json"
    }
    
    r = requests.get("https://prod.just-dance.com/songdb/v1/songs", headers=headers);
    
    return r.json()


def get_links(ubiv1_token, map_name):
    headers = {
        "User-Agent": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "Authorization": f"Ubi_v1 {ubiv1_token}",
        "X-SkuId": "jd2022-xone-all",
        "Content-Type": "application/json"
    }
    
    r = requests.get(f"https://prod.just-dance.com/content-authorization/v1/maps/{map_name}", headers=headers);
    
    return r.json()


def get_items(path):
    if path in indexed_files:
        print("taken indexed files:", path)
        return indexed_files[path]
    
    items = []
    
    for file in file_database:
        if file["url"].startswith(path):
            item_splitted = file["url"].replace(path, "").split("/")
            
            if item_splitted[0]+"/" in file["url"]:
                item_type = "folder"
            else:
                item_type = "file"
            
            if (len(items) > 0 and items[-1]["name"] == item_splitted[0]) or item_splitted[0] == "":
                continue
            
            items.append({
                "name": item_splitted[0],
                "type": item_type,
                "lastModified": file["last-modified"],
                "lastModifiedTimestamp": datetime.timestamp(dateutil.parser.parse(file["last-modified"])),
                "etag": file["md5"],
                "url": path+item_splitted[0]
            })
            
            if item_type == "folder":
                items[-1]["url"]+="/"
    
    files = list(filter(lambda x: x["type"] == "file", items))
    folders = list(filter(lambda x: x["type"] == "folder", items))
    
    files = list(sorted(files, key = lambda x: x["lastModifiedTimestamp"]))
    folders = list(sorted(folders, key = lambda x: x["name"]))
    
    indexed_files[path] = folders + files
    return indexed_files[path]


@app.route('/')
def index():
    return render_template("index.html")


# API endpoints
@app.route('/api/v1/file-list', methods=["GET"])
def file_list():
    if 'path' not in request.args:
        return abort(400)
    
    path = request.args.get('path')
    items = get_items(path)
    
    return { "items": items }


authorized_urls = {}


@app.route('/api/v1/get-download-url', methods=["GET"])
@limiter.limit("5 per minute")
def get_download_url():
    if 'url' not in request.args:
        return abort(400)
    
    url = request.args.get("url")
    if url.endswith("/"):
        return abort(400)
    
    if url.startswith("public/"):
        return {
            "url": "https://jd-s3.akamaized.net/" + url,
            "canExpire": False,
            "expirationTimestamp": None,
            "move": True,
            "message": None
        }
    
    if url.startswith("private/map"):
        map_name = url.split("/")[2]
        asset = url.split("/")[3]
        
        if asset in authorized_urls and authorized_urls[asset]["expirationTimestamp"] > time.time() + 15:
            return authorized_urls[asset]
        
        ubiv1_token = get_session(XBL3_TOKEN, "xbl3.0")["ticket"]
        
        try:
            links = get_links(ubiv1_token, map_name)
            
            auth_link = links["urls"][f"jmcs://jd-contents/{map_name}/{map_name}.ogg"]
            auth_value = auth_link.split("?auth=")[1]
            
            response = {
                "url": "https://jd-s3.akamaized.net/" + url + "?auth=" + auth_value,
                "canExpire": True,
                "expirationTimestamp": time.time() + 3600,
                "move": True,
                "message": None
            }
            
            authorized_urls[asset] = response
            return response
        except:
            return {
                "url": "https://jd-s3.akamaized.net/" + url,
                "canExpire": True,
                "expirationTimestamp": 0,
                "move": False,
                "message": "This map is not added in production servers. Website can't generate link. Sorry!"
            }
    
    return {
        "url": "https://jd-s3.akamaized.net/" + url,
        "canExpire": True,
        "expirationTimestamp": 0,
        "move": False,
        "message": "Website cannot get this file. Sorry!"
    }