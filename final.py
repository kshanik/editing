import datetime
import os
import shutil
import csv
import bpy
import pathlib

class Text:
    def __init__(self, text, start, end, font, size, x, y, color, shadow, box, bold, italic, show):
        self.text   = text
        self.start  = start
        self.end    = end
        self.font   = font
        self.size   = size
        self.x      = x
        self.y      = y
        self.color  = color
        self.shadow = shadow
        self.box    = box
        self.show   = show
        self.bold   = bold
        self.italic = italic
        # bpy.context.active_sequence_strip.align_x = 'LEFT'
        # bpy.context.active_sequence_strip.align_y = 'TOP'
        
    def __str__(self):
        return f"{self.text}, {self.start}, {self.end}, {self.font}, {self.size}, {self.x}, {self.y}, {self.color}, {self.shadow}, {self.box}"


class Clip:
    def __init__(self, file, start, end, sound, show):
        self.file  = file
        self.start = start
        self.end   = end
        self.sound = sound
        self.show  = show

    def __str__(self):
        return f"{self.file}({self.start}, {self.end}, {self.sound})"

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


def apply_fade_in_to_clip(clip_transition_overlap):
    # make sure the clips overlap
    bpy.context.active_sequence_strip.frame_start -= clip_transition_overlap
    bpy.ops.sequencer.fades_add(type="IN")

def main():
    """
    Python code to create short clips from videos and stich them back to back
    with a transition
    """
    print(pathlib.Path().absolute())
    font_directory    = r"C:\Users\msharma1\Documents\personal\pinksalt\fonts"
    video_folder_path = r"C:\Users\msharma1\Documents\personal\pinksalt\nimona"
    if len(video_folder_path) == 0:
        raise TypeError('Please provide path!')

    # uncomment the next two lines when running on macOS or Linux
    # user_folder = os.path.expanduser("~")
    # video_folder_path = f"{user_folder}/tmp/my_videos"

    set_up_output_params(video_folder_path)
    texts = []
    with open(os.path.join(video_folder_path, "final.csv"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        row_count = 0
        for row in spamreader:
            if (row_count > 0):
                texts.append(Text(
                     row[0]
                    ,int(row[1])
                    ,int(row[2])
                    ,row[3]
                    ,float(row[4])
                    ,float(row[5])
                    ,float(row[6])
                    ,row[7]
                    ,True if row[8]=='1' else False
                    ,True if row[9]=='1' else False
                    ,True if row[10]=='1' else False
                    ,True if row[11]=='1' else False
                    ,row[12]
                    )
                )
            row_count += 1
    
    for t in texts:
        print(t)

    sequence_editor = find_sequence_editor()
    sequence_editor_context = {
        "area": sequence_editor,
    }

    clean_sequencer(sequence_editor_context)
    clean_proxies(video_folder_path)

    start_frame_pos = 0
    for text in texts:
        if text.show == '1':
            start = text.start
            end   = text.end
            count = end-start+1
            bpy.ops.sequencer.effect_strip_add(sequence_editor_context, type='TEXT', frame_start=start, frame_end=end, channel=1)
            bpy.context.active_sequence_strip.frame_start = start-1
            bpy.context.active_sequence_strip.frame_final_duration = count
            bpy.context.active_sequence_strip.text = text.text
            bpy.context.active_sequence_strip.font_size = text.size
            bpy.context.active_sequence_strip.location[0] = text.x
            bpy.context.active_sequence_strip.location[1] = text.y
#            bpy.context.active_sequence_strip.align_x = 'LEFT'
#            bpy.context.active_sequence_strip.align_y = 'TOP'
            bpy.context.active_sequence_strip.use_shadow = text.shadow
            bpy.context.active_sequence_strip.use_box = text.box
            color_in_hex = text.color
            color = tuple(float(int(color_in_hex[i:i+2], 16))/256 for i in (0, 2, 4, 6))
            bpy.context.active_sequence_strip.color = color
            bpy.context.active_sequence_strip.use_bold = text.bold
            bpy.context.active_sequence_strip.use_italic = text.italic
            bpy.ops.font.open(filepath=font_directory+os.sep+'BAUHS93.TTF')
            start_frame_pos += count

    # Set the final frame
    if bpy.context.active_sequence_strip:
        bpy.context.scene.frame_end = bpy.context.active_sequence_strip.frame_final_end

    # Render the clip sequence
    # bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
