#!/usr/bin/python3.5
import mutagen
import os
import subprocess
import argparse
from multiprocessing import Pool,current_process,cpu_count
from shutil import copyfile
from mutagen.mp3 import MP3

# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <boerni@pakke.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return 
# ----------------------------------------------------------------------------


prefix=None
bitrate=None

def copy_id3(srcname, destname):
    src = mutagen.File(srcname, easy=True)
    dest = mutagen.File(destname, easy=True)
    for k in src:
        try:
            dest[k] = src[k]
        except:
            continue
    dest.save()

def reencode_mp3(path):
    f=MP3(path)
    if bitrate < int(f.info.bitrate / 1000):
        subprocess.call(("lame","--quiet","-b",str(bitrate),path,prefix+path))
    else:
        copyfile(path,prefix+path)
        
def reencode_m4a(path):
    tmpfile=str(current_process().name)+".wav"
    subprocess.call(("faad","-q","-o",tmpfile,path))
    subprocess.call(("lame","--quiet","-b",str(bitrate),tmpfile,prefix+path[:-3]+"mp3"))
    copy_id3(path,prefix+path[:-3]+"mp3")
    os.remove(tmpfile)

def reencode_wma(path):
    tmpfile=str(current_process().name)+".wav"
    subprocess.call(("ffmpeg","-y","-i",path,tmpfile))
    subprocess.call(("lame","--quiet","-b",str(bitrate),tmpfile,prefix+path[:-3]+"mp3"))
    copy_id3(path,prefix+path[:-3]+"mp3")
    os.remove(tmpfile)

def reencode_flac(path):
    subprocess.call(("flac","-d","-f",path))
    subprocess.call(("lame","--quiet","-b",str(bitrate),path[:-4]+"wav",prefix+path[:-4]+"mp3"))
    copy_id3(path,prefix+path[:-4]+"mp3")
    os.remove(path[:-4]+"wav")

def reencode_ogg(path):
    subprocess.call(("oggdec",path))
    subprocess.call(("lame","--quiet","-b",str(bitrate),path[:-3]+"wav",prefix+path[:-3]+"mp3"))
    copy_id3(path,prefix+path[:-3]+"mp3")
    os.remove(path[:-3]+"wav")

def reencode_mpc(path):
    tmpfile=str(current_process().name)+".wav"
    subprocess.call(("mpcdec",path,tmpfile))
    subprocess.call(("lame","--quiet","-b",str(bitrate),tmpfile,prefix+path[:-3]+"mp3"))
    copy_id3(path,prefix+path[:-3]+"mp3")
    os.remove(tmpfile)

if __name__ == "__main__":
    #argstuff
    parser=argparse.ArgumentParser(description='resize your music! runs parallel, keeps your ID3 tags, skips already-small files')
    parser.add_argument('-w',type=int,default=cpu_count(),help="how many processes to use")
    parser.add_argument('-i',type=str,default="Musik",help="Input-directory")
    parser.add_argument('-o',type=str,default="klein",help="Prefix for the Output-directory")
    parser.add_argument('-b',type=int,default=128,help="Target-Bitrate")
    args=parser.parse_args()
    pool = Pool(args.w)
    prefix=args.o
    bitrate=args.b
    for root, dirs, files in os.walk(args.i, topdown=False):
        if not os.path.isdir(prefix+root):
            os.makedirs(prefix+root)
        for name in files:
            if name.lower().endswith("mp3"):
                pool.apply_async(reencode_mp3,(os.path.join(root, name),))
            elif name.lower().endswith("flac"):
                pool.apply_async(reencode_flac,(os.path.join(root, name),))
            elif name.lower().endswith("ogg"):
                pool.apply_async(reencode_ogg,(os.path.join(root,name),))
            elif name.lower().endswith("wma"):
                pool.apply_async(reencode_wma,(os.path.join(root, name),))
            elif name.lower().endswith("mpc"):
                pool.apply_async(reencode_mpc,(os.path.join(root, name),))
            elif name.lower().endswith("m4a"):
                pool.apply_async(reencode_m4a,(os.path.join(root, name),))
    pool.close()
    pool.join()
