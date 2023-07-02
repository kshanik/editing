import math
import datetime
import os
import shutil
import csv
import bpy
import pathlib
import pandas as pd
from .fonts import get_font_file

scene_end_frame = 0
start_frame_pos = 0
video_folder_path = ''
right_bite_path = ''
fonts = {}

def get_font(f):
    global fonts
    if f not in fonts:
        fonts[f] = bpy.data.fonts.load(get_font_file(f))
    else:
        print('Font already loaded!')
    return fonts[f]

class Text:
    def __init__(self, text, start, end, font, size, x, y, color, shadow, box, box_color, bold, italic, channel, group, show):
        self.text   = text
        self.start  = start
        self.end    = end
        self.font   = font
        self.size   = size
        self.x      = x
        self.y      = 1.0-y
        self.color  = color
        self.shadow = shadow
        self.box    = box
        self.box_color    = box_color
        self.bold   = bold
        self.italic = italic
        self.channel = channel
        self.group   = group
        self.show   = show

    def __str__(self):
        return f"{self.text},{self.start},{self.end},{self.font},{self.size},{self.x},{self.y},{self.color},{self.shadow},{self.box},{self.bold},{self.italic},{self.channel},{self.show}"

class Image:
    def __init__(self, file, start, end, x, y, scale_x, scale_y, channel, show):
        self.file       = file
        self.start      = start
        self.end        = end
        self.x          = 1920*x - 1920/2.0
        self.y          = 1080/2.0 - 1080*y
        self.scale_x    = scale_x
        self.scale_y    = scale_y
        self.channel    = channel
        self.show       = show
        
    def __str__(self):
        return f"{self.file} = {self.start}, {self.end}, {self.x}, {self.y}, {self.scale_x}, {self.scale_y}, {self.channel}, {self.show}"

class Color:
    def __init__(self, color, start, end, x, y, scale_x, scale_y, channel, show):
        self.color      = color
        self.start      = start
        self.end        = end
        self.x          = 1920*x - 1920/2.0
        self.y          = 1080/2.0 - 1080*y
        self.scale_x    = scale_x
        self.scale_y    = scale_y
        self.channel    = channel
        self.show       = show
        
    def __str__(self):
        return f"{self.color},{self.start},{self.end},{self.x},{self.y},{self.scale_x},{self.scale_y},{self.channel},{self.show}"

class Clip:
    def __init__(self, file, start, end, sound, effect, channel, show):
        self.file  = file
        self.start = start
        self.end   = end
        self.sound = sound
        self.effect  = effect
        self.channel = channel
        self.show  = show

    def __str__(self):
        return f"{self.file}({self.start}, {self.end}, {self.sound},{self.channel},{self.show})"

class Audio:
    def __init__(self, file, start, end, sound, channel, show):
        self.file  = file
        self.start = start
        self.end   = end
        self.sound = sound
        self.channel = channel
        self.show  = show

    def __str__(self):
        return f"{self.file}({self.start}, {self.end}, {self.sound},{self.channel},{self.show})"

def clean_sequencer(sequence_context):
    bpy.ops.sequencer.select_all(sequence_context, action="SELECT")
    bpy.ops.sequencer.delete(sequence_context)

def find_sequence_editor():
    for area in bpy.context.window.screen.areas:
        if area.type == "SEQUENCE_EDITOR":
            return area
    return None

def set_up_output_params(folder_path):
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.constant_rate_factor = "PERC_LOSSLESS"

    now = datetime.datetime.now()
    time = now.strftime("%H-%M-%S")
    filepath = os.path.join(folder_path, f"stitched_together_{time}.mp4")
    scene.render.filepath = filepath

def add_clip(context, clip):
    global video_folder_path
    global start_frame_pos
    start = int(clip.start)
    end   = int(clip.end)
    count = end-start+1
    print(start, end, count)
    video_name = clip.file
    # create a full path to the video
    video_path = os.path.join(video_folder_path, video_name)
    print(f"Processing video {video_path}")
    # add video to the sequence editor
    before = bpy.data.scenes['Scene'].sequence_editor.sequences_all.keys()
    bpy.ops.sequencer.movie_strip_add(
        context,
        filepath=video_path,
        directory=video_folder_path + os.sep,
        channel=clip.channel,
        sound=True,
        overlap=True,
        replace_sel=True
        )
    after = bpy.data.scenes['Scene'].sequence_editor.sequences_all.keys()
    delta = set(after)-set(before)
    fps = 50
    clips = []
    for d in delta:
        clip_start_offset_frame = start-1
        movie = bpy.data.scenes['Scene'].sequence_editor.sequences_all[d]
        trim_the_video(movie, clip_start_offset_frame, count)
        move_the_clip_into_position(movie, start_frame_pos, clip_start_offset_frame)
        print('movie.type', movie.type)
        if movie.type == 'SOUND':
            movie.volume = float(clip.sound)
        if 'MOVIE' in movie.type:
            fps = movie.fps
            print('fps is ->>', fps)
        clips.append(movie)

    for c in clips:
        if clip.effect != 'NO':
            apply_fade_in_to_clip(c, fps)
    start_frame_pos = bpy.context.active_sequence_strip.frame_final_end

def add_text(context, text):
    print('add_text', text)
    bpy.ops.sequencer.effect_strip_add(context, type='TEXT', frame_start=text.start, frame_end=text.end, channel=text.channel)
    bpy.context.active_sequence_strip.frame_start = text.start
    bpy.context.active_sequence_strip.frame_final_duration = text.end-text.start+1
    bpy.context.active_sequence_strip.text = text.text
    bpy.context.active_sequence_strip.font_size = text.size
    bpy.context.active_sequence_strip.location[0] = text.x
    bpy.context.active_sequence_strip.location[1] = text.y
    #bpy.context.active_sequence_strip.align_x = 'LEFT'
    #bpy.context.active_sequence_strip.align_y = 'TOP'
    bpy.context.active_sequence_strip.use_shadow = text.shadow
    bpy.context.active_sequence_strip.use_box = text.box
    color_in_hex = text.box_color
    color = tuple(float(int(color_in_hex[i:i+2], 16))/256 for i in (0, 2, 4, 6))
    bpy.context.active_sequence_strip.box_color = color
    color_in_hex = text.color
    color = tuple(float(int(color_in_hex[i:i+2], 16))/256 for i in (0, 2, 4, 6))
    bpy.context.active_sequence_strip.color = color
    bpy.context.active_sequence_strip.use_bold = text.bold
    bpy.context.active_sequence_strip.use_italic = text.italic
    bpy.context.active_sequence_strip.font = get_font(text.font)

def add_color(context, color):
    print('add_color', color)
    bpy.ops.sequencer.effect_strip_add(context, type='COLOR', frame_start=color.start, frame_end=color.end, channel=color.channel)
    bpy.context.active_sequence_strip.transform.scale_x = color.scale_x
    # bpy.context.active_sequence_strip.transform.keyframe_insert(data_path="scale_x", frame=1)
    # bpy.context.active_sequence_strip.transform.scale_x = 0
    # bpy.context.active_sequence_strip.transform.keyframe_insert(data_path="scale_x", frame=100)
    bpy.context.active_sequence_strip.transform.scale_y = color.scale_y
    bpy.context.active_sequence_strip.transform.offset_x = color.x
    bpy.context.active_sequence_strip.transform.offset_y = color.y
    color_in_hex = color.color
    color = tuple(float(int(color_in_hex[i:i+2], 16))/256 for i in (0, 2, 4))
    print('color->',color)
    bpy.context.active_sequence_strip.color = color

def add_image(context, image):
    print(image)
    bpy.ops.sequencer.image_strip_add(context
        , directory=os.path.dirname(image.file)
        , files=[{ "name": os.path.basename(image.file)}]
        , channel=image.channel)
    bpy.context.active_sequence_strip.frame_start = image.start
    bpy.context.active_sequence_strip.frame_final_duration = image.end-image.start+1
    bpy.context.active_sequence_strip.transform.offset_x = image.x
    bpy.context.active_sequence_strip.transform.offset_y = image.y
    bpy.context.active_sequence_strip.transform.scale_x = image.scale_x
    bpy.context.active_sequence_strip.transform.scale_y = image.scale_y

def add_audio(context, audio):
    print(audio)
    bpy.ops.sequencer.sound_strip_add(
          filepath=audio.file
        , directory=os.path.dirname(audio.file)
        , files=[{"name": audio.file}]
        , frame_start=audio.start, channel=audio.channel)
    bpy.context.active_sequence_strip.frame_final_duration = audio.end - audio.start + 1
    bpy.context.active_sequence_strip.volume = audio.sound

def clean_proxies(video_folder_path):
    """
    This will delete the BL_proxies folder
    """

    def on_error(function, path, excinfo):
        print(f"Failed to remove {path}\n{excinfo}")

    bl_proxy_path = os.path.join(video_folder_path, "BL_proxy")
    if os.path.exists(bl_proxy_path):
        print(f"Removing the BL_proxies folder in {bl_proxy_path}")
        shutil.rmtree(bl_proxy_path, ignore_errors=False, onerror=on_error)


def trim_the_video(movie, clip_start_offset_frame, clip_frame_count):
    # trim the start of the clip
    movie.frame_offset_start = clip_start_offset_frame

    # trim the end of the clip
    movie.frame_final_duration = clip_frame_count


def move_the_clip_into_position(movie, start_frame_pos, clip_start_offset_frame):
    movie.frame_start = start_frame_pos - clip_start_offset_frame

def apply_fade_in_to_clip(strip, clip_transition_overlap):
    # make sure the clips overlap
    strip.frame_start -= clip_transition_overlap
    bpy.ops.sequencer.fades_add(type="IN")

def updateEndFrame():
    global scene_end_frame
    if bpy.context.active_sequence_strip.frame_final_end > scene_end_frame:
        scene_end_frame = bpy.context.active_sequence_strip.frame_final_end

def getClips(i, items):
    clips = []
    while i < len(items):
        if isinstance(items[i][0], float) and math.isnan(items[i][0]) == True:
            break
        clips.append(Clip(
              items[i][0]
            , items[i][1]
            , items[i][2]
            , items[i][3]
            , items[i][4]
            , int(items[i][5])
            , True if items[i][6]==1 else False)
        )
        i += 1
    return clips, i

def getTexts(i, items):
    texts = []
    while i < len(items):
        if isinstance(items[i][0], float) and math.isnan(items[i][0]) == True:
            break
        text = items[i][0]
        group = False
        if ';' in text:
            text = text.replace(';', '\n')
            group = True
        texts.append(Text(
             text
            ,int(items[i][1])
            ,int(items[i][2])
            ,items[i][3]
            ,float(items[i][4])
            ,float(items[i][5])
            ,float(items[i][6])
            ,items[i][7]
            ,True if items[i][8]==1 else False
            ,True if items[i][9]==1 else False
            ,items[i][10]
            ,True if items[i][11]==1 else False
            ,True if items[i][12]==1 else False
            ,int(items[i][13])
            ,group
            ,True if items[i][14]==1 else False
            ))
        i += 1
    return texts, i

def getImages(i, items, video_path):
    images = []
    # Add Image functionality!
    while i < len(items):
        if isinstance(items[i][0], float) and math.isnan(items[i][0]) == True:
            break
        images.append(Image(
            video_path + os.sep + items[i][0]
            ,int(items[i][1])
            ,int(items[i][2])
            ,float(items[i][3])
            ,float(items[i][4])
            ,float(items[i][5])
            ,float(items[i][6])
            ,int(items[i][7])
            ,True if items[i][8]==1 else False
            ))
        i += 1

    return images, i

def getAudios(i, items, video_path):
    audios = []
    while i < len(items):
        if isinstance(items[i][0], float) and math.isnan(items[i][0]) == True:
            break
        audios.append(Audio(
             video_path + os.sep + items[i][0]
            , int(items[i][1])
            , int(items[i][2])
            , float(items[i][3])
            , int(items[i][4])
            , True if items[i][5]==1 else False
            ))
        i += 1
    return audios, i

def getColors(i, items):
    colors = []
    while i < len(items):
        if isinstance(items[i][0], float) and math.isnan(items[i][0]) == True:
            break
        colors.append(Color(
              items[i][0]
            , int(items[i][1])
            , int(items[i][2])
            , float(items[i][3])
            , float(items[i][4])
            , float(items[i][5])
            , float(items[i][6])
            , int(items[i][7])
            , True if items[i][8]==1 else False
            ))
        i += 1
    return colors, i

def clear():
    global scene_end_frame
    global start_frame_pos
    sequence_editor = find_sequence_editor()
    sequence_editor_context = {
        "area": sequence_editor,
    }
    clean_sequencer(sequence_editor_context)
    scene_end_frame = 0
    start_frame_pos = 0
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end   = 100

def clear_all(excel, sheet):
    clear()
    excel_dir = os.path.dirname(excel)
    video_folder_path = excel_dir + os.sep + sheet
    clean_proxies(video_folder_path)

def final(excel, sheet):
    """
    Python code to create short clips from videos and stich them back to back
    with a transition
    """
    global video_folder_path
    global start_frame_pos
    global scene_end_frame
    global right_bite_path

    excel_dir = os.path.dirname(excel)
    font_directory    = excel_dir + os.sep + "fonts"
    video_folder_path = excel_dir + os.sep + sheet
    right_bite_path = excel_dir

    os.chdir(video_folder_path)

    set_up_output_params(video_folder_path)
    texts = []
    images = []
    audios = []
    clips = []
    colors = []
    rows = pd.read_excel(excel,sheet, header=None)
    print(rows)
    items = rows.values.tolist()
    print(items)
    i = 0
    while i < len(items):
        print('item ', items[i][0])
        if isinstance(items[i][0], float) and math.isnan(items[i][0]) == True:
            i+=1
            continue
        elif items[i][0] == 'clip':
            _clips, i = getClips(i+1, items)
            clips += _clips
        elif items[i][0] == 'text':
            _texts, i = getTexts(i+1, items)
            texts += _texts
        elif items[i][0] == 'image':
            _images, i = getImages(i+1, items, video_folder_path)
            images += _images
        elif items[i][0] == 'color':
            _colors, i = getColors(i+1, items)
            colors += _colors
        elif items[i][0] == 'sound':
            _audios, i = getAudios(i+1, items, video_folder_path)
            audios += _audios
        i+=1

    for t in texts:
        print('text', t)

    for t in images:
        print('image', t)

    for t in audios:
        print('audio', t)

    for t in colors:
        print('color', t)

    for t in clips:
        print('clip', t)

    sequence_editor = find_sequence_editor()
    sequence_editor_context = {
        "area": sequence_editor,
    }

    clear()

    for clip in clips:
        print('cl', clip)
        if clip.show == 1:
            add_clip(sequence_editor_context, clip)
            updateEndFrame()

    print('channel->>', bpy.context.active_sequence_strip.channel)

    bpy.ops.sequencer.select_all(action='SELECT')
    bpy.ops.sequencer.meta_make()

    for audio in audios:
        print(audio)
        if audio.show == True:
            add_audio(sequence_editor_context, audio)
            updateEndFrame()

    for color in colors:
        if color.show == True:
            add_color(sequence_editor_context, color)
            updateEndFrame()

    for text in texts:
        if text.show == True:
            # if text.group:
            #     lines = text.text.splitlines()
            #     max_len = 0
            #     for l in lines:
            #         if max_len < len(l):
            #             max_len = len(l)
            #     text_width  = (text.size * max_len) / 1.333
            #     text_height = ((text.size * len(lines)) / 1.333) + ((len(lines)-1) * ((text.size / 1.333)*0.589041095890411))
            #     text_height += 100
            #     add_color(sequence_editor_context, 
            #         Color('ffffffff', text.start, text.end, text.x, text.y
            #         , text_width/1920, text_height/1080, text.channel-1, 1))
                # start = text.start
                # odd_even = True
                # while start < text.end:
                #     if odd_even == True:
                #         bpy.context.active_sequence_strip.transform.scale_x += 0.05
                #         bpy.context.active_sequence_strip.transform.scale_y += 0.05
                #         bpy.context.active_sequence_strip.transform.keyframe_insert(data_path="scale_x", frame=start)
                #         bpy.context.active_sequence_strip.transform.keyframe_insert(data_path="scale_y", frame=start)
                #         odd_even = False
                #     else:
                #         bpy.context.active_sequence_strip.transform.scale_x -= 0.05
                #         bpy.context.active_sequence_strip.transform.scale_y -= 0.05
                #         bpy.context.active_sequence_strip.transform.keyframe_insert(data_path="scale_x", frame=start)
                #         bpy.context.active_sequence_strip.transform.keyframe_insert(data_path="scale_y", frame=start)
                #         odd_even = True
                #     start += 50
            add_text(sequence_editor_context, text)
            updateEndFrame()

    for image in images:
        print(image)
        if image.show == True:
            add_image(sequence_editor_context, image)
            updateEndFrame()

    bpy.context.scene.frame_end = scene_end_frame

    # bpy.ops.sequencer.effect_strip_add(sequence_editor_context, type='COLOR', frame_start=1, frame_end=100, channel=1)
    # bpy.context.active_sequence_strip.color[0] = 1
    # bpy.context.active_sequence_strip.color[1] = 0
    # bpy.context.active_sequence_strip.color[2] = 0
    # bpy.context.active_sequence_strip.transform.scale_x = 0.4
    # bpy.context.active_sequence_strip.transform.keyframe_insert(data_path="scale_x", frame=1)
    # bpy.context.active_sequence_strip.transform.scale_x = 0
    # bpy.context.active_sequence_strip.transform.keyframe_insert(data_path="scale_x", frame=100)
    # bpy.context.active_sequence_strip.transform.scale_y = 0.001
    # bpy.context.active_sequence_strip.transform.offset_x = 0
    # bpy.context.active_sequence_strip.transform.offset_y = -421

    # Render the clip sequence
    # bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
