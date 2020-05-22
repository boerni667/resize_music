#!/usr/bin/python3
import mutagen
import os
import subprocess
import argparse
import traceback
from multiprocessing import Pool,current_process,cpu_count
from shutil import copyfile, which
from mutagen.mp3 import MP3
from mutagen.aac import AAC
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
    spltfld[-1] = _format
    return '.'.join(spltfld)


def encode(_format, _bitrate, src, tgt):
    if _format == "mp3":
        subprocess.call(("lame", "--quiet", "-b", str(_bitrate), src, tgt), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif _format == "aac":
        subprocess.call(("faac", "-v0", "-b", str(_bitrate), "-o", tgt, src), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def copy_id3(srcname, destname):
    try:
        src = mutagen.File(srcname, easy=True)
        dest = mutagen.File(destname, easy=True)
        for k in src:
            try:
                dest[k] = src[k]
            except:
                continue
        dest.save()
    except Exception as e:
        with open("errors.txt", 'a') as f:
            traceback.print_exc(file=f)


def reencode_mp3(path):
    try:
        if encoding == "mp3":
            f = MP3(path)
            if bitrate < int(f.info.bitrate / 1000)+10:
                encode(encoding, bitrate, path, prefix+path)
            else:
                copyfile(path, prefix+path)
        elif encoding == "aac":
            tmpfile = "/tmp/" + str(uuid4()) + ".wav"
            target_file = change_ending(prefix + path, encoding)
            subprocess.call(("mpg321", "-w", tmpfile, path),stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            encode(encoding, bitrate, tmpfile, target_file)
            copy_id3(path, target_file)
            os.remove(tmpfile)
            
    except Exception as e:
        with open("errors.txt", 'a') as f:
            traceback.print_exc(file=f)


def reencode_m4a(path):
    try:
        source_bitrate = int(AAC(path).info.bitrate / 1000)
    except mutagen.aac.AACError:
        source_bitrate = 5000
    try:
        target_file = change_ending(prefix + path, encoding)
        if encoding == "mp3" or source_bitrate > bitrate:
            tmpfile = "/tmp/" + str(uuid4()) + ".wav"
            subprocess.call(("faad", "-q", "-o", tmpfile, path),stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            encode(encoding, bitrate, tmpfile, target_file)
            copy_id3(path, target_file)
            os.remove(tmpfile)
        elif encoding == "aac" and source_bitrate <= bitrate+10:
            copyfile(path, target_file)
    except Exception as e:
        with open("errors.txt", 'a') as f:
            traceback.print_exc(file=f)


def reencode_wma(path):
    try:
        tmpfile = "/tmp/" + str(uuid4()) + ".wav"
        target_file = change_ending(prefix + path, encoding)
        subprocess.call(("ffmpeg", "-y", "-i", path, tmpfile),stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        encode(encoding, bitrate, tmpfile, target_file)
        copy_id3(path, target_file)
        os.remove(tmpfile)
    except Exception as e:
        with open("errors.txt", 'a') as f:
            traceback.print_exc(file=f)


def reencode_flac(path):
    try:
        tmpfile = "/tmp/" + str(uuid4()) + ".wav"
        target_file = change_ending(prefix + path, encoding)
        subprocess.call(("flac", "-d", "-f", path, "-o", tmpfile),stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        encode(encoding, bitrate, tmpfile, target_file)
        copy_id3(path, target_file)
        os.remove(tmpfile)
    except Exception as e:
        with open("errors.txt", 'a') as f:
           traceback.print_exc(file=f)

def reencode_ogg(path):
    try:
        tmpfile = change_ending(path, "wav")
        target_file = change_ending(prefix + path, encoding)
        subprocess.call(("oggdec", path),stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        encode(encoding, bitrate, tmpfile, target_file)
        copy_id3(path, target_file)
        os.remove(tmpfile)
    except Exception as e:
        with open("errors.txt", 'a') as f:
            traceback.print_exc(file=f)


def reencode_mpc(path):
    try:
        tmpfile = "/tmp/" + str(uuid4()) + ".wav"
        target_file = change_ending(prefix+path, encoding)
        subprocess.call(("mpcdec", path, tmpfile),stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        encode(encoding, bitrate, tmpfile, target_file)
        copy_id3(path, target_file)
        os.remove(tmpfile)
    except Exception as e:
        with open("errors.txt",'a') as f:
            traceback.print_exc(file=f)


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
    args=parser.parse_args()
    pool = Pool(args.w, initializer=init, initargs=(args.o, args.b, args.t))
    for root, dirs, files in os.walk(args.i, topdown=False):
        if not os.path.isdir(args.o+root):
            os.makedirs(args.o+root)
        for name in files:
            ending = name.split(".")[-1].lower()
            if ending == "mp3":
                pool.apply_async(reencode_mp3, (os.path.join(root, name),))
            elif ending == "flac":
                pool.apply_async(reencode_flac, (os.path.join(root, name),))
            elif ending == "ogg":
                pool.apply_async(reencode_ogg, (os.path.join(root,name),))
            elif ending == "wma":
                pool.apply_async(reencode_wma, (os.path.join(root, name),))
            elif ending == "mpc":
                pool.apply_async(reencode_mpc, (os.path.join(root, name),))
            elif ending in ["m4a", "aac"]:
                pool.apply_async(reencode_m4a, (os.path.join(root, name),))
    pool.close()
    pool.join()
