#Purpose

fifproc.py will batch update the stim channel of a fif file, removing meaningless zero values and adjusting the timing of the stim channel to match the timing of the photodiode channel.

Run 
```bash
./fifproc.py -h
```
for usage information.

#ASSUMPTIONS ABOUT THE DATA
* Stim channel changes **BEFORE** photodiode changes
* Zero values in stim channel are meaningless, and should be overwritten with the last value of the stim channel
* Distances between photodiode values on adjacent screens are much larger than variation in photodiode value on a single screen

#DEFAULT VALUES
* Input stim channel is STI101
* Input photodiode channel is MISC007
* Output stim channel is STI101
* Reasonable thresholding value for the photodiode data is 0.4
