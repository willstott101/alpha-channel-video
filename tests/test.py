#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "Pillow",
#   "numpy",
# ]
# ///

import os
import array
import shutil
import subprocess
from PIL import Image
import numpy as np

TEST_IMAGES_DIR = "assets/test_cubes_render"


def encode_video(path, extra_args=()):
	return subprocess.run([
		"ffmpeg",
		"-framerate",
		"12",
		"-pattern_type",
		"glob",
		"-i",
		f"{TEST_IMAGES_DIR}/*.webp",
		"-y", # overwrite
		*extra_args,
		# output file
		path
	])


def decode_video(path, extra_args=()):
	output_dir_path = f"{path}.decoded/"

	if os.path.exists(output_dir_path):
		shutil.rmtree(output_dir_path)
	os.mkdir(output_dir_path)

	process = subprocess.run([
		"ffmpeg",
		*extra_args,
		"-i",
		path,
		# .bmp does not have RGBA out of ffmpeg :(
		# .webp does not work for image sequences... only outputs one file
		f"{output_dir_path}%04d.png",
	])


def psnr(img1, img2):
    mse = np.mean((np.asarray(img1, dtype=np.float32) - np.asarray(img2, dtype=np.float32)) ** 2)
    if mse == 0:
        return float('inf')
    PIXEL_MAX = 255.0
    return 20 * np.log10(PIXEL_MAX / np.sqrt(mse))


def compare_files(path_orig, path_out):
	img_orig = Image.open(path_orig)
	img_out = Image.open(path_out)
	return psnr(img_orig, img_out)


def compare_folders(path_orig, path_out):
	missing = []
	same = []
	different = []
	files_out = sorted(os.listdir(path_out))
	for file_orig in sorted(os.listdir(path_orig)):
		name, ext = file_orig.rsplit(".", 1)
		for file_out in files_out:
			out_name = file_out.rsplit(".", 1)[0]
			if out_name == name:
				dist = compare_files(os.path.join(path_orig, file_orig), os.path.join(path_out, file_out))
				print("dist", dist, file_orig, file_out)
				if dist > 33:
					same.append(file_orig)
				else:
					different.append(file_orig)
				break
		else:
			missing.append(file_orig)

	return {
		"missing": missing,
		"same": same,
		"different": different,
	}


encode_video("results/ffmpeg_libvpx-vp9.webm", extra_args=[ "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "2"])
decode_video("results/ffmpeg_libvpx-vp9.webm", extra_args=["-vcodec", "libvpx-vp9"])
results = compare_folders(TEST_IMAGES_DIR, "results/ffmpeg_libvpx-vp9.webm.decoded")
print(results)


encode_video("results/ffmpeg_libvpx-vp9.mkv", extra_args=[ "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "2"])
decode_video("results/ffmpeg_libvpx-vp9.mkv", extra_args=["-vcodec", "libvpx-vp9"])
results = compare_folders(TEST_IMAGES_DIR, "results/ffmpeg_libvpx-vp9.mkv.decoded")
print(results)


# encode_video("results/ffmpeg_libvpx-vp9.mp4", extra_args=[ "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "2"])
# decode_video("results/ffmpeg_libvpx-vp9.mp4", extra_args=["-vcodec", "libvpx-vp9"])
# results = compare_folders(TEST_IMAGES_DIR, "results/ffmpeg_libvpx-vp9.mp4.decoded")
# print(results)


# encode_video("results/ffmpeg_libaom-av1.mkv", extra_args=[ "-c:v", "libaom-av1", "-b:v", "0", "-crf", "20", "-pix_fmt", "yuva420p"])
# decode_video("results/ffmpeg_libaom-av1.mkv", extra_args=[])
# results = compare_folders(TEST_IMAGES_DIR, "results/ffmpeg_libaom-av1.mkv.decoded")
# print(results)
