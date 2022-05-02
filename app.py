from fastapi import FastAPI, Response, Request, Depends, Header, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from datetime import datetime
from config import XBL3_TOKEN
import dateutil.parser
import requests
import nanoid
import time
import json

app = FastAPI(docs_url=None, openapi_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")

current_sessions = {}

with open("file_database.json") as f:
    file_database = json.load(f)

@app.get("/")
def index():
    return HTMLResponse(open("index.html", encoding="utf-8").read())

@app.put("/api/v2/sessions", status_code=201)
def create_session():
    session_id = nanoid.generate()
    
    start_time = time.time()
    die_time = start_time + 10
    
    current_sessions[session_id] = {
        "start_time": start_time,
        "die_time": die_time,
    }
    
    return {
        "sessionId": session_id,
        "startTime": start_time,
        "dieTime": die_time
    }

@app.delete("/api/v2/sessions/{session_id}")
def delete_session(session_id: str, response: Response):
    if session_id not in current_sessions:
        response.status_code = 404
        return {
            "removed": False,
            "reason": "Session is not found."
        }
    
    current_sessions.pop(session_id)
    return {
        "removed": True
    }

async def check_session(x_session_id: str = Header(...)):
    if x_session_id not in current_sessions:
        raise HTTPException(status_code=400, detail="Session not found")
    
    current_sessions[x_session_id]["die_time"] = time.time() + 10
    
    return x_session_id

@app.get("/api/v2/ping", dependencies=[Depends(check_session)]) 
def ping():
    return {
        "pong": True
    }

indexed_items = {}
auth_cookies = {}

banned_maps = []

def get_items(path):
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
                "lastModified": datetime.timestamp(dateutil.parser.parse(file["last-modified"])),
                "url": "/" + path + item_splitted[0]
            })
            
            if item_type == "folder":
                items[-1]["url"] += "/"
    
    files = list(filter(lambda x: x["type"] == "file", items))
    folders = list(filter(lambda x: x["type"] == "folder", items))
    
    files = list(sorted(files, key = lambda x: x["lastModified"]))
    folders = list(sorted(folders, key = lambda x: x["name"]))
    
    return items

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

@app.get("/api/v2/objects/check-directory", dependencies=[Depends(check_session)])
def get_directory_list(path: str, skip: int, limit: int, generateContentAuthorization: bool):
    if path not in indexed_items:
        indexed_items[path] = get_items(path[1::])
    
    has_more = False
    if skip + limit < len(indexed_items[path]):
        objects = indexed_items[path][skip : skip+limit]
        has_more = True
    else:
        objects = indexed_items[path][skip::]
    
    result = {
        "objects": objects,
        "hasMore": has_more,
    }
    
    if generateContentAuthorization and path.startswith("/private/map/"):
        map_name = path.split("/")[3]
        if map_name != "" or map_name in banned_maps:
            try:
                if map_name in auth_cookies and auth_cookies[map_name]["timestamp"] > time.time() + 15:
                    auth_value = auth_cookies[map_name]["cookie"]
                else:
                    ubiv1_token = get_session(XBL3_TOKEN, "xbl3.0")["ticket"]

                    links = get_links(ubiv1_token, map_name)
                
                    auth_link = links["urls"][f"jmcs://jd-contents/{map_name}/{map_name}.ogg"]
                    auth_value = auth_link.split("?auth=")[1]
                    
                    auth_cookies[map_name] = {
                        "cookie": auth_value,
                        "timestamp": time.time() + 3600
                    }
                
                for index in range(len(objects)):
                    if objects[index]["type"] == "file":
                        objects[index]["authorizedUrl"] = "https://jd-s3.akamaized.net" + objects[index]["url"] + "?auth=" + auth_value
                        objects[index]["cannotGenerateLink"] = False
                        objects[index]["authorizedUrlExpiration"] = auth_cookies[map_name]["timestamp"]
            except:
                for index in range(len(objects)):
                    if objects[index]["type"] == "file":
                        objects[index]["cannotGenerateLink"] = True
                banned_maps.append(map_name)
    
    return result