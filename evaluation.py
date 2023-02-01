'''
This module generates a report of the results of applying the chyron detection tool.
'''

import requests
import subprocess
import tempfile
import mmif
import os
import json
from glob import glob

APP_URL = "http://0.0.0.0:5001/"

video_file_paths = glob("/Users/kelleylynch/data/clams/video/*.mp4")
for video_file_path in video_file_paths:
    with tempfile.NamedTemporaryFile() as fout:
        out = subprocess.run(["clams", "source", f"video:{video_file_path}"], stdout=fout)
        fout.seek(0)
        empty_mmif = fout.read()

    if True:
        params_list = [
        ]
        for params in params_list:
            print (f"Running Slate App with params {params}")
            resp = requests.post(APP_URL,
                                data=empty_mmif,
                                params=params
                                )
            result_mmif = mmif.Mmif(resp.json())
            with open(f"/Users/kelleylynch/data/clams/chyrondetetion/{os.path.basename(video_file_path[:-4])}.mmif", 'w') as out:
                json.dump(resp.json(), out)

