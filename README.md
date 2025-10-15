| Container     | Codec         | FFmpeg Status | Blender Status |
| ------------- | ------------- | ------------- | -------------- |
| WebM          | VP9           | Works*        | Works          |

`*`: Must specify `-vcodec libvpx-vp9` when encoding/decoding with ffmpeg directly (blender does this automatically). See: https://trac.ffmpeg.org/ticket/8344


Hopeful future option will be x265 mov - only in ffmpeg 8+
Hopeful far-future option will be AV2 - no specified support for RGBA that I see but lots of focus on multi-stream / "layered" content.
