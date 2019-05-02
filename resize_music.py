#!/usr/bin/python3.5
import mutagen
import os
import subprocess
import argparse
import traceback
from multiprocessing import Pool,current_process,cpu_count
from shutil import copyfile
from mutagen.mp3 import MP3

# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <boerni@pakke.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return 
# ----------------------------------------------------------------------------



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
        with open("errors.txt",'a') as f:
            traceback.print_exc(file=f)

def reencode_mp3(path):
    try:
        f=MP3(path)
        if bitrate < int(f.info.bitrate / 1000):
            subprocess.call(("lame","--quiet","-b",str(bitrate),path,prefix+path))
        else:
            copyfile(path,prefix+path)
    except Exception as e:
        with open("errors.txt",'a') as f:
            traceback.print_exc(file=f)
        
def reencode_m4a(path):
    try:
        tmpfile=str(current_process().name)+".wav"
        subprocess.call(("faad","-q","-o",tmpfile,path))
        subprocess.call(("lame","--quiet","-b",str(bitrate),tmpfile,prefix+path[:-3]+"mp3"))
        copy_id3(path,prefix+path[:-3]+"mp3")
        os.remove(tmpfile)
    except Exception as e:
        with open("errors.txt",'a') as f:
            traceback.print_exc(file=f)

def reencode_wma(path):
    try:
        tmpfile=str(current_process().name)+".wav"
        subprocess.call(("ffmpeg","-y","-i",path,tmpfile))
        subprocess.call(("lame","--quiet","-b",str(bitrate),tmpfile,prefix+path[:-3]+"mp3"))
        copy_id3(path,prefix+path[:-3]+"mp3")
        os.remove(tmpfile)
    except Exception as e:
        with open("errors.txt",'a') as f:
            traceback.print_exc(file=f)

def reencode_flac(path):
    global bitrate
    try:
        tmpfile="/tmp/"+str(current_process().name)+".wav"
        subprocess.call(("flac","-d","-f",path,"-o",tmpfile))
        subprocess.call(("lame","--quiet","-b",str(bitrate),tmpfile,tmpfile[:-3]+"mp3"))
        subprocess.call(("cp",tmpfile[:-3]+"mp3",prefix+path[:-3]+"mp3"))
        copy_id3(path,prefix+path[:-3]+"mp3")
        os.remove(tmpfile)
        os.remove(tmpfile[:-3]+"mp3")
    except Exception as e:
        with open("errors.txt",'a') as f:
            traceback.print_exc(file=f)

def reencode_ogg(path):
    try:
        subprocess.call(("oggdec",path))
        subprocess.call(("lame","--quiet","--quiet","-b",str(bitrate),path[:-4]+"wav",prefix+path[:-4]+"mp3"))
        copy_id3(path,prefix+path[:-3]+"mp3")
        os.remove(path[:-3]+"wav")
    except Exception as e:
        with open("errors.txt",'a') as f:
            traceback.print_exc(file=f)

def reencode_mpc(path):
    try:
        tmpfile=str(current_process().name)+".wav"
        subprocess.call(("mpcdec",path,tmpfile))
        subprocess.call(("lame","--quiet","-b",str(bitrate),tmpfile,prefix+path[:-3]+"mp3"))
        copy_id3(path,prefix+path[:-3]+"mp3")
        os.remove(tmpfile)
    except Exception as e:
        with open("errors.txt",'a') as f:
            traceback.print_exc(file=f)
            
def init(p,b):
    global prefix
    global bitrate
    prefix=p
    bitrate=b
    
if __name__ == "__main__":
    #argstuff
    parser=argparse.ArgumentParser(description='resize your music! runs parallel, keeps your ID3 tags, skips already-small files')
    parser.add_argument('-w',type=int,default=cpu_count(),help="how many processes to use")
    parser.add_argument('-i',type=str,default="Musik",help="Input-directory")
    parser.add_argument('-o',type=str,default="klein",help="Prefix for the Output-directory")
    parser.add_argument('-b',type=int,default=128,help="Target-Bitrate")
    args=parser.parse_args()
    pool = Pool(args.w,initializer=init,initargs=(args.o,args.b,))
    for root, dirs, files in os.walk(args.i, topdown=False):
        if not os.path.isdir(args.o+root):
            os.makedirs(args.o+root)
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
