import math
import datetime
import os
import shutil
import csv
import bpy
import pandas as pd


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

def cut(excel, sheet):
    """
    Python code to create short clips from videos and stich them back to back
    with a transition
    """
    excel_dir = os.path.dirname(excel)
    video_folder_path = excel_dir + os.sep + sheet

    os.chdir(video_folder_path)

    set_up_output_params(video_folder_path)
    clips = []
    rows = pd.read_excel(excel,sheet)
    items = rows.values.tolist()
    for l in items:
        print(type(l[0]),type(l[1]),type(l[2]),type(l[3]),type(l[4]))
        if isinstance(l[0], float) and math.isnan(l[0]):
            break
        else:
            clips.append(Clip(l[0],l[1],l[2],l[3],l[4]))

    for c in clips:
        print (c.file, c.start, c.end, c.sound, c.show)

    sequence_editor = find_sequence_editor()

    sequence_editor_context = {
        "area": sequence_editor,
    }
    clean_sequencer(sequence_editor_context)
    clean_proxies(video_folder_path)
    start_frame_pos = 0
    for clip in clips:
        print(clip)
        if clip.show == 1:
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
                sequence_editor_context,
                filepath=video_path,
                directory=video_folder_path + os.sep,
                channel=1,
                sound=True)
            after = bpy.data.scenes['Scene'].sequence_editor.sequences_all.keys()
            delta = set(after)-set(before)
            for d in delta:
                clip_start_offset_frame = start-1
                movie = bpy.data.scenes['Scene'].sequence_editor.sequences_all[d]
                trim_the_video(movie, clip_start_offset_frame, count)
                move_the_clip_into_position(movie, start_frame_pos, clip_start_offset_frame)
                if movie.type == 'SOUND':
                    movie.volume = float(clip.sound)
            start_frame_pos += count

    # Set the final frame
    if bpy.context.active_sequence_strip:
        bpy.context.scene.frame_end = bpy.context.active_sequence_strip.frame_final_end
    print('Done cutting!')
    # Render the clip sequence
    # bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    cut()
