import cv2
import os
from moviepy.editor import *

path = './static/images'
output = './static/videos'
nameof_video = '/newvideo.mp4'
audiofpath='./static/music/Happy_birthday_to_you_MIDI(chosic.com).mp3' 
outputpath = output+nameof_video
imageslist = os.listdir(path)

j = 0
for i in imageslist:
    i = path + '/' + i
    imageslist[j] = i
    j += 1

clips=[]
for i in range(len(imageslist)):
    clips.append(ImageClip(imageslist[i]).set_duration(2))
video_clip=concatenate_videoclips(clips,method='compose')

videofile=VideoFileClip(outputpath)
audio_bg=AudioFileClip(audiofpath)
final_audio=audio_bg


video_clip=video_clip.set_audio(final_audio)
video_clip.write_videofile(outputpath,fps=24,remove_temp=True)
