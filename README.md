# IKEA-project

## How to run

- Run api server
```
pip install -r requirements.txt
set FLASK_APP=api/main.py
flask run
```

- Run client
```
git submodule init          # When git clone first
git submodule update        # When client is updated
cd client && npm install
npm run serve
```
