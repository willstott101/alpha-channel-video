| Container     | Codec         | FFmpeg Status | Blender Status |
| ------------- | ------------- | ------------- | -------------- |
| webm          | VP9           | OK*           | Works          |
| mkv           | VP9           | OK*           | ?              |
| mp4           | VP9           | FAIL          | ?              |
| webm          | AV1           | FAIL          | ?              |


`*`: Must specify `-vcodec libvpx-vp9` when decoding with ffmpeg directly (blender does this automatically). See: https://trac.ffmpeg.org/ticket/8344


Hopeful future option will be x265 mov - only in ffmpeg 8+
Hopeful far-future option will be AV2 - no specified support for RGBA that I see but lots of focus on multi-stream / "layered" content.


Run tests with:
* `./tests/test.py`
Requires `uv` to be on the path.


Notes:
* ffmpeg rgba video -> bmp does not maintain alpha, but video -> png sequence does
* ffmpeg can accept webp image sequences but not output them 
