#!/usr/bin/env python

import os
import datetime
from PIL import Image
 
VIDEO_EXTENTIONS_UPPER = ['MP4', 'AVI', 'MOV']
TIMESTAMP_RESOLUTION = datetime.timedelta(seconds=1)
MIN_TIMELAPSE_INTERVAL = datetime.timedelta(seconds=1)
MIN_TIMELAPSE_LENGTH = 5

def get_exif(filename):
    """Return dictionary of recognized EXIF keys in header of given JPEG file.
    """

    from PIL.ExifTags import TAGS

    exifdata = {}
    im = Image.open(filename)
    rawexifdata = im._getexif()
    for rawkey, value in rawexifdata.iteritems():
        if rawkey in TAGS:
            decodedkey = TAGS[rawkey]
            ret[decodedkey] = value
    im.close()
    return ret


def find_timelapses(directory, return_timestamps=False, return_images=False,
                    return_videos=False):
    """Detect timelapse image sequences based on timestamps.

    From a directory containing images and videos, possibly in subdirectories,
    detect timelapse image sequences and classify files into images, videos 
    and timelapse sequences.

    Parameters
    ----------
    directory : str
        Path to top-level directory containing images.
    return_timestamps : bool, optional
        For all images, return (filename, timestamp) tuples rather than just
        filename.
    return_images : bool, optional
        Return list of single images in addition to list of timelapses.
    return_videos : bool, optional
        Return list of videos in addition to list of timelapses.

    Returns
    -------
    timelapses : list
        List of lists of filenames of images in each timelapse group.
    images : list
        List of filenames of images. Only returned if `return_images` is True.
    videos : list
        List of filenames of videos. Only returned if `return_videos` is True.
    
    Notes
    -----
    Videos are detected based on filename extension only.
    """

    # Check that input directory exists
    if not (os.path.exists(directory) and os.path.isdir(directory)):
        raise ValueError('Directory does not exist: {}'.format(directory))

    # Walk through the subdirectories and inspect each file for image-ness
    # and timestamp.
    videos = []  # This will contain filenames
    images = []  # This will contain tuples of (filename, timestamp).
    for root, dirs, files in os.walk(directory):
        for f in files:
            fullname = '{}/{}'.format(root, f)

            # Try to open it with PIL. If PIL can't open it, check if it
            # is a video based on the extention name, then move on.
            try:
                im = Image.open(fullname)
            except IOError:
                if '.' in f:
                    ext = f.split('.')[-1].upper()
                    if ext in VIDEO_EXTENTIONS_UPPER:
                        videos.append(fullname)
                continue

            # Get the string timestamp in appropriate manner depending on
            # the image format.
            if im.format == 'JPEG':
                rawexifdata = im._getexif()
                timestamp = rawexifdata[36867]
            elif im.format == 'TIFF':
                timestamp = im.tag[36867]
            else:
                raise IOError('Unable to read header of image format:'
                              ' {} in file {}'.format(im.format, fullname))

            # Append the image's filename and timestamp.
            images.append((fullname, timestamp))

    # Sort images by their (string) timestamps.
    images = sorted(images, key=lambda image: image[1])

    # Initialize containers and loop values.
    timelapses = []
    singleimages = []
    lasttime = None
    elapsed = None
    imagegroup = []
    imagegroup_interval = None
    for image in images:
        
        start_new_imagegroup = False
        
        # Get this image's timestamp in a `datetime` object.
        date, time = image[1].split()
        year, month, day = date.split(':')
        hour, minute, sec = time.split(':')
        thistime = datetime.datetime(int(year), int(month), int(day),
                                     int(hour), int(minute), int(sec))

        # If lasttime is not yet defined, this is the first image.
        # Start a new imagegroup and move on.
        if lasttime is None:
            imagegroup.append(image)
            lasttime = thistime
            continue

        elapsed = thistime - lasttime  # Calculate elapsed time.

        # If the elapsed time is very small (i.e., 0), this can't part of
        # a timelapse with the currently accumulating imagegroup. (It is
        # probably part of a group of continuous exposure shots). Start a
        # new imagegroup.
        if elapsed < MIN_TIMELAPSE_INTERVAL:
            start_new_imagegroup = True

        # If the imagegroup only has 1 image, add this image and set the 
        # interval of the imagegroup.
        elif len(imagegroup) == 1:
            imagegroup.append(image)
            imagegroup_interval = elapsed
 
        # Otherwise, we have an imagegroup going. See if this elapsed time
        # matches the interval of the imagegroup
        elif (abs(elapsed - imagegroup_interval) <= TIMESTAMP_RESOLUTION):
            imagegroup.append(image)
            
        # If it doesn't match, the current image isn't part of a timelapse
        # with the previous images.
        else: 
            start_new_imagegroup = True

        if start_new_imagegroup:
            # Check length of the currently accumulating imagegroup
            # to see if we should save the imagegroup as a timelapse,
            # or save the individual images.
            if len(imagegroup) >= MIN_TIMELAPSE_LENGTH:
                timelapses.append(imagegroup)
            else:
                singleimages.extend(imagegroup)

            # Restart the imagegroup with the current image.
            imagegroup = [image]
            imagegroup_interval = None

        lasttime = thistime # prepare for next loop

    # Clean up any remaining images in imagegroup
    if len(imagegroup) >= MIN_TIMELAPSE_LENGTH:
        timelapses.append(imagegroup)
    else:
        singleimages.extend(imagegroup)    

    # Get return values.
    if not return_timestamps:
        singleimages = [image[0] for image in singleimages]
        for i in range(len(timelapses)):
            timelapses[i] = [image[0] for image in timelapses[i]]

    if return_images and return_videos:
        return timelapses, singleimages, videos
    if return_images and not return_videos: 
        return timelapses, singleimages
    if return_videos and not return_images:
        return timelapses, videos
    else:
        return timelapses
