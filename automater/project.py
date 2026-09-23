import json
import os

import cv2

from . import actions as A


class Project:
    def __init__(self, path: str):
        self.path = path
        self.images_dir = os.path.join(path, "images")
        self.steps = []

    @property
    def json_path(self):
        return os.path.join(self.path, "project.json")

    def ensure_dirs(self):
        os.makedirs(self.images_dir, exist_ok=True)

    def new_image_path(self, tag: str) -> str:
        self.ensure_dirs()
        idx = len(os.listdir(self.images_dir)) if os.path.isdir(self.images_dir) else 0
        return os.path.join(self.images_dir, f"{idx:04d}_{tag}.png")

    def save_image(self, path: str, bgr_image) -> None:
        cv2.imwrite(path, bgr_image)

    def save(self):
        self.ensure_dirs()
        data = {"steps": [A.to_dict(s) for s in self.steps]}
        with open(self.json_path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> "Project":
        proj = cls(path)
        with open(proj.json_path) as f:
            data = json.load(f)
        proj.steps = [A.from_dict(d) for d in data["steps"]]
        return proj
