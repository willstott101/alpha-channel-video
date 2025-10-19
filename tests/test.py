#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "Pillow",
#   "numpy",
#   "blessings",
# ]
# ///

import os
import array
import shutil
import subprocess
from PIL import Image
import numpy as np
from multiprocessing.pool import ThreadPool
import pprint
from blessings import Terminal

t = Terminal()

TEST_IMAGES_DIR = "assets/test_cubes_render"


def encode_video(path, extra_args=()):
	return subprocess.run(
		[
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
		],
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		stdin=subprocess.DEVNULL,
	)


def decode_video(path, extra_args=()):
	output_dir_path = f"{path}.decoded/"

	if os.path.exists(output_dir_path):
		shutil.rmtree(output_dir_path)
	os.mkdir(output_dir_path)

	return subprocess.run(
		[
			"ffmpeg",
			*extra_args,
			"-i",
			path,
			# .bmp does not have RGBA out of ffmpeg :(
			# .webp does not work for image sequences... only outputs one file
			f"{output_dir_path}%04d.png",
		],
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		stdin=subprocess.DEVNULL,
	)


def psnr(img1, img2):
    mse = np.mean((img1 - img2) ** 2)
    if mse == 0:
        return float('inf')
    PIXEL_MAX = 255.0
    return 20 * np.log10(PIXEL_MAX / np.sqrt(mse))


def compare_files(path_orig, path_out):
	img_orig = Image.open(path_orig)
	img_orig = np.asarray(img_orig, dtype=np.float32)
	img_out = Image.open(path_out)
	img_out = np.asarray(img_out, dtype=np.float32)
	if img_orig.shape != img_out.shape:
		# Resolution or number of channels are different, similarity is 0...
		return 0
	return psnr(img_orig, img_out)


def compare_folders(path_orig, path_out):
	missing = []
	similar = []
	different = []
	files_out = sorted(os.listdir(path_out))
	for file_orig in sorted(os.listdir(path_orig)):
		name, ext = file_orig.rsplit(".", 1)
		for file_out in files_out:
			out_name = file_out.rsplit(".", 1)[0]
			if out_name == name:
				dist = compare_files(os.path.join(path_orig, file_orig), os.path.join(path_out, file_out))
				if dist > 33:
					similar.append((file_orig, dist))
				else:
					different.append((file_orig, dist))
				break
		else:
			missing.append(file_orig)

	return {
		"missing": missing,
		"similar": similar,
		"different": different,
	}


def roundtrip(out_file, *, encode_args=(), decode_args=()):
	encode_process = encode_video(out_file, extra_args=encode_args)
	decode_process = decode_video(out_file, extra_args=decode_args)
	comparison = compare_folders(TEST_IMAGES_DIR, f"{out_file}.decoded")
	return {
		"encode_process": encode_process,
		"decode_process": decode_process,
		"comparison": comparison,
	}


if __name__ == "__main__":
	# result_types:
	#  ALL_SIMILAR - roundtripped images are almost identical
	#  ALL_INCOMPARABLE - roundtripped images are not of the same size/depth/mode

	tests = [
		dict(
			out_path="results/ffmpeg_libvpx-vp9.webm",
			encode_args=["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "2"],
			decode_args=["-vcodec", "libvpx-vp9"],
			expected_result="ALL_SIMILAR",
		),
		dict(
			out_path="results/ffmpeg_libvpx-vp9.mkv",
			encode_args=["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "2"],
			decode_args=["-vcodec", "libvpx-vp9"],
			expected_result="ALL_SIMILAR",
		),
		dict(
			out_path="results/ffmpeg_libvpx-vp9.mp4",
			encode_args=["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "2"],
			decode_args=["-vcodec", "libvpx-vp9"],
			expected_result="ALL_INCOMPARABLE", # The MP4 conatiner format has no standard for vp9 yuva
		),
		dict(
			out_path="results/ffmpeg_libaom-av1.webm",
			encode_args=["-c:v", "libaom-av1", "-b:v", "0", "-crf", "20", "-pix_fmt", "yuva420p"],
			# decode_args=[],
			expected_result="ALL_INCOMPARABLE", # There seems to be no AV1 yuva standard...
		),
	]

	def run_test(cfg):
		r = roundtrip(
			cfg["out_path"],
			encode_args=cfg.get("encode_args", ()),
			decode_args=cfg.get("decode_args", ()),
		)
		PASS = f"{t.green}PASS{t.normal}"
		FAIL = f"{t.red}FAIL{t.normal}"
		ERROR = f"{t.red}ERROR{t.normal}"
		EXPECTED_FAIL = f"{t.yellow}EXPECTED_FAIL{t.normal}"

		error_messages = []
		if cfg["expected_result"] == "ALL_SIMILAR":
			result = PASS
			if r["comparison"]["missing"]:
				error_messages.append("some output frames are missing")
				result = FAIL
			if r["comparison"]["different"]:
				error_messages.append("some output frames differ")
				result = FAIL
		elif cfg["expected_result"] == "ALL_INCOMPARABLE":
			result = EXPECTED_FAIL
			if r["comparison"]["missing"]:
				error_messages.append("some/all output frames are missing")
				result = FAIL
			if r["comparison"]["similar"]:
				error_messages.append("some/all output frames are similar")
				result = FAIL
			if any(similarity != 0 for name, similarity in r["comparison"]["different"]):
				error_messages.append("some/all output frames are comparable")
				result = FAIL
		else:
			error_messages.append(f"unknown expected_result: {cfg['expected_result']!r}")
			result = ERROR

		return {
			"out_path": cfg["out_path"],
			"result": result,
			"error_messages": error_messages,
		}


	p = ThreadPool(4)
	results = p.map(run_test, tests)
	for result in results:
		print(result["result"], result["out_path"])
		if result["error_messages"]:
			pprint.pprint(result["error_messages"])
