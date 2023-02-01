import requests
import subprocess
import tempfile
import os
import json
from glob import glob
from typing import List


def run_video_directory(file_path_list: List[str], app_url, app_name, data_directory):
    for video_file_path in file_path_list:
        with tempfile.NamedTemporaryFile() as fout:
            subprocess.run(["clams", "source", f"video:{video_file_path}"], stdout=fout)
            fout.seek(0)
            empty_mmif = fout.read()

        params_list = [
            {}        
        ]
        for _ind, params in enumerate(params_list):
            print(f"Running App with params {params}")
            resp = requests.post(app_url,
                                 data=empty_mmif,
                                 params=params
                                 )
            output_filename = os.path.basename(os.path.splitext(video_file_path)[0])
            if len(params_list) > 1:
                output_filename = f"{output_filename}_{_ind}"
            output_filename += ".mmif"
            output_filename = os.path.join(data_directory, "mmif", app_name, output_filename)
            with open(output_filename, 'w') as out:
                json.dump(resp.json(), out)


if __name__ == '__main__':
    import argparse
    argparse = argparse.ArgumentParser()
    argparse.add_argument("--app_url", default="http://0.0.0.0:5001/")
    argparse.add_argument("--app_name", default="chyrondetection")
    argparse.add_argument("--data_directory", default="/data")
    args = argparse.parse_args()
    video_file_paths = glob(os.path.join(args.data_directory, "video", "*.mp4"))
    run_video_directory(video_file_paths, args.app_url, args.app_name, args.data_directory)
