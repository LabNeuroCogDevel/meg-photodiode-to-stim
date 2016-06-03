#!/usr/bin/python3

# ASSUMPTIONS ABOUT THE DATA
# - Stim channel changes BEFORE photodiode changes
# - Zero values in stim channel should be overwritten with the last
#   value of the stim channel
# - Distances between photodiode values on adjacent screens are much
#   larger than variation in photodiode value on a single screen
# DEFAULT VALUES
# - Input stim channel is STI101
# - Input photodiode channel is MISC007
# - Output stim channel is STI101
# - Reasonable thresholding value for the photodiode data is 0.4

from __future__ import print_function

import re
import mne
import getopt
import os.path as op
import numpy as np
from sys import argv
from matplotlib import pyplot as plt

stim_default_name='STI101'
diode_default_name='MISC007'

# thresholds an array from left to right to remove small variations
def threshold(arr,t):
    last=float("-inf")
    for i in range(len(arr)):
        if abs(arr[i]-last)>t:
            last=arr[i]
        else:
            arr[i]=last

# returns true if x and y are not equal within tolerance t
def floatne(x,y,t=0.001):
    return abs(x-y) > t
    

# removes the zeros in an array by filling in a block of zeros with the
# last nonzero value
def remove_zeros(arr):
    lastvalue=0
    for i in range(len(arr)):
        if floatne(arr[i],0):
            lastvalue=arr[i]
        else:
            arr[i]=lastvalue


# assumes trigger changes, then guide changes,
# and that this repeats
def guide_by(trigger,guide):
    lasttrigger=trigger[0]
    lookingforguide=False
    i=1
    while i < min(len(guide),len(trigger)):
        if lookingforguide:
            if floatne(guide[i],guide[i-1]):
                lasttrigger=trigger[i]
                lookingforguide=False
            else:
                trigger[i]=lasttrigger
        else:
            if floatne(trigger[i],lasttrigger):
                lookingforguide=True
                trigger[i]=lasttrigger
        i+=1

# test the above functions on a stimulus array
# and a photodiode array
def test(stim,diode):
    d0=diode.copy()
    d1=d0.copy()
    threshold(d1,0.4)
    s0=stim.copy()
    s1=s0.copy()
    remove_zeros(s1)
    s2=s1.copy()
    guide_by(s2,d1)
    return ([s0,s1,s2],[d0,d1])

# plot the STI101 and MISC007 channels of a raw file for debug reasons
def plotraw(raw):
    chans=raw.copy().pick_channels(['STI101','MISC007'])
    tt=range(chans._data.shape[1])
    plt.plot(tt,chans._data.T,'.-')
    plt.show()
    

# plot the results of test for debug reasons
def plotthem(tt,dd,ss,plotter):
    for i in range(2):
        for j in range(3):
            plotter.subplot(3,2,1+2*j+i)
            plotter.plot(tt,dd[i],'.-')
            plotter.plot(tt,ss[j],'.-')
            plotter.ylabel("diode {0}, stim {1}".format(i,j))
    plotter.show()


# given a raw file, use the functions to process the data
# and remove zeros and move the stimulus channel.
def process_raw(raw,
                stimulus_channel_name='STI101',
                diode_channel_name='MISC007',
                out_channel_name='STI101',
                t=0.4):
    raw=raw.copy()
    raw.load_data()
    chans=raw.copy().pick_channels([stimulus_channel_name,diode_channel_name])
    cd=chans._data
    stim=cd[0]
    diode=cd[1]
    threshold(diode,t)
    remove_zeros(stim)
    guide_by(stim,diode)
    i=raw.info['ch_names'].index(out_channel_name)
    for j in range(len(raw._data[i])):
        raw._data[i][j]=stim[j]
    return raw

# if run as a script, print the help information
def show_help(filename):
    print(filename,'[-h][-s stimulus_channel_name][-d diode_channel_name]')
    print('    [-S stimulus_and_out_shared_channel_name][-o output_channel_name][-t threshold] FILENAME [FILENAMES]')
    print('')
    print("Ignores file names that don't end with .fif (case insensitive), and those that end with .STIM_PROC.fif")
    print('')
    print('long arg equivalents are:')
    print('  -h --help')
    print('  -s --stimulus')
    print('  -d --diode')
    print('  -o --outchannel')
    print('  -t --threshold')
    

if __name__=='__main__':
    script_name = op.basename(__file__)
    stch_name = stim_default_name
    dich_name = diode_default_name
    out_name = stim_default_name
    thresh=0.4
    try:
        opts, args = getopt.getopt(argv,'hs:d:o:t:',['stimulus','diode','outchannel','threshold','help'])
    except getopt.GetOptError:
        show_help(script_name)
        sys.exit(1)
    if len(args)==0:
        print('No file names were passed to the script.')
        show_help(script_name)
        sys.exit(0)
    for (opt,arg) in opts:
        if opt in ('-h','--help'):
            show_help(script_name)
            sys.exit(0)
        elif opt in ('-s','--stimulus'):
            stch_name=arg
        elif opt in ('-d','--diode'):
            dich_name=arg
        elif opt=='-S':
            stch_name=out_name=arg
        elif opt in ('-o','--outchannel'):
            out_name=arg
        elif opt in ('-t','--threshold'):
            thresh=float(arg)
            if thresh <= 0:
                print('error, threshold needs to be positive, given:',thresh)
                sys.exit(2)
    for argfile in args:
        root,ext = op.splitext(argfile)
        r2,ext2 = op.splitext(root)
        if (not re.fullmatch('[.]fif',ext,re.IGNORECASE)) or ext2 == '.STIM_PROC':
            print(argfile,'already processed, or not a .fif. Skipping...')
            continue
        new_path = "".join([root,'.STIM_PROC',ext])
        if op.exists(new_path):
            print(new_path,'the file where the processed version of',argfile,'would be saved already exists. Skipping...')
            continue
        raw = mne.io.RawFIF(argfile,verbose=False)
        raw2 = process_raw(raw, stch_name, dich_name, out_name, thresh)
        raw2.save(new_path)

    



