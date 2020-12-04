#!/usr/bin/python3
import mutagen
import os
import subprocess
import argparse
import traceback
from multiprocessing import Pool,current_process,cpu_count
from shutil import copyfile, which
from uuid import uuid4
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <boerni@pakke.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return 
# ----------------------------------------------------------------------------


for tool in ["faac",
             "faad",
             "ffmpeg",
             "flac",
             "lame",
             "mpcdec",
             "mpg321",
             "oggdec"
             ]:
    if not which(tool):
        print(tool + " missing!\nexiting. If you think you don't need this tool, e.g. you miss flac but don't have any FLAC files, try uncommenting it out from the list in line 20.")
        quit(-1)


def change_ending(name, _format):
    spltfld = name.split('.')
    if len(spltfld)>1:
        spltfld[-1] = _format
    else:
        spltfld.append(_format)
    return '.'.join(spltfld)


def remove(path):
    if os.path.exists(path):
        os.remove(path)


def transform(_format, _in, _out):
    toDelete = []
    try:
        if _format == "mp3":  # decode
            call_obj = ("mpg321", "-w", _out, _in)
            toDelete.append(change_ending(_out, "wav"))
        elif _format == "faad":  # decode
            call_obj = ("faad", "-q", "-o", _out, _in)
            toDelete.append(change_ending(_out, "wav"))
        elif _format == "wma":  # decode
            call_obj = ("ffmpeg", "-y", "-i", _in, _out)
            toDelete.append(change_ending(_out, "wav"))
        elif _format == "flac":  # decode
            call_obj = ("flac", "-d", "-f", _in, "-o", _out)
            toDelete.append(change_ending(_out, "wav"))
        elif _format == "ogg":  # decode
            call_obj = ("oggdec", _in)
            toDelete.append(change_ending(_in, "wav"))
        elif _format == "mpc":  # decode
            call_obj = ("mpcdec", _in, _out)
            toDelete.append(_out)
        elif _format == "lame":  # encode
            call_obj = ("lame", "--quiet", "-b", str(bitrate), _in, _out)
        elif _format == "aac":  # encode
            call_obj = ("faac", "-v0", "-b", str(bitrate), "-o", _out, _in)
            toDelete.append(change_ending(_in, "wav"))
        else:
            raise ValueError("{} not supported".format(_format))
        with open("{}-stdout.txt".format(current_process().name),"at") as sout, open("{}-stderr.txt".format(current_process().name),"at") as serr:
            subprocess.call(call_obj, stdout=sout, stderr=serr)
    except Exception as e:
        with open("errors.txt", 'a') as f:
            traceback.print_exc(file=f)
    return toDelete

def copy_id3(srcname, destname):
    if not encoding == "aac":
        src = mutagen.File(srcname, easy=True)
        dest = mutagen.File(destname, easy=True)
        for k in src:
            dest[k] = src[k]
        dest.save()
    #except Exception as e:
        #with open("errors.txt", 'a') as f:
            #traceback.print_exc(file=f)


def reencode_generic2wav2target(path, codec):
    toDelete = []
    tmpfile = "/tmp/" + str(uuid4()) + ".wav"
    target_file = change_ending(prefix + path, encoding)
    toDelete + transform(codec, path, tmpfile)
    toDelete + transform(encoding, tmpfile, target_file)
    toDelete.append(tmpfile)
    copy_id3(path, target_file)
    for item in toDelete:
        remove(item)


def reencode_native(path, source_codec):
    try:
        source_bitrate = int(mutagen.File(path).info.bitrate / 1000)
    except (mutagen.aac.AACError, mutagen.mp3.MP3Error):
        source_bitrate = 5000
    if encoding == source_codec and source_bitrate <= bitrate+10:
        copyfile(path, prefix+path)
    elif encoding == source_codec and encoding == "mp3" and source_bitrate > bitrate+10:
        transform("lame", path, prefix+path)
    else:
        reencode_generic2wav2target(path, source_codec)


def init(p, b, e):
    global prefix
    global bitrate
    global encoding
    prefix = p
    bitrate = b
    encoding = e


if __name__ == "__main__":
    #argstuff
    parser=argparse.ArgumentParser(description='resize your music! runs parallel, keeps your ID3 tags, skips already-small files')
    parser.add_argument('-w', type=int, default=cpu_count(), help="how many processes to use")
    parser.add_argument('-i', type=str, default="Musik", help="Input-directory")
    parser.add_argument('-o', type=str, default="klein", help="Prefix for the Output-directory")
    parser.add_argument('-t', type=str, default="mp3", help="Target Encoding, support for MP3 and M4A. While MP3 is more available on end user devices, AAC offers better quality on lower bitrates.")
    parser.add_argument('-b', type=int, default=128, help="Target-Bitrate")
    parser.add_argument('-debug', action='store_true', default=False, help="disable multiprocessing for debugging")
    args=parser.parse_args()
    if not args.debug:
        pool = Pool(args.w, initializer=init, initargs=(args.o, args.b, args.t))
    else:
        init(args.o, args.b, args.t)
    for root, dirs, files in os.walk(args.i, topdown=False):
        if not os.path.isdir(args.o+root):
            os.makedirs(args.o+root)
        for name in files:
            ending = name.split(".")[-1].lower()
            if ending in ["mpc", "wma", "ogg", "flac"]:
                if not args.debug:
                    pool.apply_async(reencode_generic2wav2target, (os.path.join(root, name), ending,))
                else:
                    reencode_generic2wav2target(os.path.join(root, name), ending)
            elif ending in ["m4a", "aac", "mp3"]:
                if not args.debug:
                    pool.apply_async(reencode_native, (os.path.join(root, name), ending,))
                else:
                    reencode_native(os.path.join(root, name), ending)
    if not args.debug:
        pool.close()
        pool.join()
