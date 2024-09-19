## 1. Installation
- python 3.8.10
- create virtual env `python3 -m venv $env_path`
- install env by `pip install -r requirements.txt`
- config log at `./backend/app/config/log` log at `./storage/log`
- config search mode at `./backend/app/conf/searcher.yaml`:
  + V0 - Local (priority)/Internet Search: `local_search: 2`, `internet_search: 2`
  + V1 - NO-Local/Internet Search: `local_search: 0`, `internet_search: 0`, `search_with_emotion: True`
  + V2 - Local Search (only): `local_search: 2`, `internet_search: 0`

## 2. Build frontend source (static html)
- Run:
```
    cd backend
    chmod +x deploy/start_build_frontend.sh
    sh deploy/start_build_frontend.sh
```
-> deploy BE as usual

## 3. Run in local/debug
- Activate and update env
```
    cd backend
    source $env_path/bin/activate
    pip install -r requirements.txt
```

- Run app by `main.py` or `uvicorn` as below:
```
    cd backend
    python main.py

    uvicorn main:app --host localhost --port 5001
    uvicorn main:app --host <host> --port <port>
```

-> Go to http://<host>:<port>

## 4. Testing local server(172.16.7.61)
- Activate and update env as usual.
- Build frontend source as usual.
- Start background service:
```
    cd backend
    chmod +x deploy/start.sh
    sh deploy/start.sh
```
-> Go to http://<host>:<port>

*NOTE*:
- Existing env: `/home/vagrant/workspace/SCG/envs/chat_dn` --> update if needed
- Host: `172.16.7.61`
- Port: `5001`(default) --> update if needed

## 5. Deploy Azure
- see `../README.md`
