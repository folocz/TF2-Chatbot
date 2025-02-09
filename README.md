# An integration of chatgpt into Team Fortress 2 chat.

## prerequisites
* tf2 launch options: `-condebug -conclearlog -usercon -g15`
* tf2 `autoexec.cfg`:
```
ip 0.0.0.0
rcon_password <password>
net_start
```

## setup
Crate a file `config.ini` similar to `config_example.ini`.
Run the following in the repo directory:
* Windows (untested):
```
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
```
* Linux/Mac:
```
python3 -m venv .venv
source .venv\Scripts\activate
python3 -m pip install -r requirements.txt
```

## running
* launch tf2
Run the following in the repo directory:
* Windows (untested):
```
.venv\Scripts\activate
py main.py
```
* Linux/Mac:
```
source .venv\Scripts\activate
python3 main.py
```
