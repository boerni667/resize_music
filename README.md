# resize_music

got a big digital music-collection and want to use it on a somewhat smaller mobile device like a USB Drive in your car-stereo or your smartphone?

don't care about quality while using it on your shitty mobile speakers/headphones?

your collection is too big?

resize_music is for the rescue!


reencodes your complete music to fix (low) bitrate mp3's. Currently supports mp3, flac, ogg, musepack, wma and m4a.

neat features:
* runs parallel on multiple cores
* keeps the ID3 tags
* skips MP3's which already have a low bitrate

needs lame, flac, oggdec, mpcdec, ffmpeg and faad and the python mutagen package.


just edit the file and adjust path to source, prefix to add for the new collection and the target bitrate. Also creates the filestructure.

published under the beer-ware license
