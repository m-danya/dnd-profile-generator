# DnD profile generator

Create a beautiful printout for your DnD character

#### Development status

45% is done


### How to host

##### Frontend

```bash
cd frontend
npm i
npm start
```

##### Backend

```bash
# install python and libraries into venv
cd backend
sudo apt install python3.9
python3.9 -m pip install virtualenv
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# run the backend
uvicorn main:app
```
