import os
import sys
import time
import subprocess
from pydub import AudioSegment
import threading
import platform
import shutil
import requests
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, HttpRequest
import json
import random
from urllib.parse import urlparse
from colorama import init, Fore, Style
import re
from datetime import timedelta

# Inicializa colorama
init(autoreset=True)

############## VARIABLES ##############

# Definir ruta base
base_path = os.path.dirname(os.path.abspath(__file__))
cores = os.cpu_count() # Cantidad de procesadores disponibles

# Endpoint suno api
base_api_suno_url = 'http://localhost:3000'

# Variables de YouTube
description = ""  # Descripción opcional del video
tags = []  # Etiquetas opcionales del video
category_id = ""  # ID de la categoría del video (Ej. 10 para Música)
privacy_status = ""  # Estado de privacidad del video (Ej. unlisted para no listado)

#datos para ejecutar la api DEZGO
url_api = "https://api.dezgo.com/"
api_key = "DEZGO-EF5AF98400D97B80A918240CBF4A5DFC08444CE2B66F58414F509A6D429293351D57FD46"
api_endpoint ="text2image_flux"
api_width = 1385
api_height = 735
api_sampler = "auto"
api_model_id = "juggernautxl_9_lightning_1024px"
api_negative_prompt = ""
api_seed = ""
api_format = "jpg"
api_guidance = 2
api_transparent_background = False

#datos para ejecutar la api Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly', 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_SECRET_FILE = os.path.join(base_path, "credentials.json") # Nombre de tu archivo de credenciales JSON
TOKEN_FILE = os.path.join(base_path, "token.json")
FOLDER_NAME = 'audio'
DOWNLOAD_PATH = os.path.join(base_path, "in", "audios")
AUDIO_MIME_TYPES = [
    'audio/mpeg',
    'audio/mp3',
    'audio/wav',
]
FOLDER_UPLOAD_PATH = os.path.join(base_path, "out", "videos")
FOLDER_UPLOAD_NAME = 'final'

#datos para ejecutar la api YouTube
YOUTUBE_SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
SCOPES_PARTNER = ['https://www.googleapis.com/auth/youtubepartner']
YOUTUBE_CLIENT_SECRET_FILE = os.path.join(base_path, "youtube_credentials.json")

############# FUNCIONES GENERALES #############

def create_folders(base_path):
    audio_folder_path = os.path.join(base_path, "in", "audios")
    image_folder_path = os.path.join(base_path, "in", "imagenes")
    video_folder_path = os.path.join(base_path, "in", "videos")
    inverted_folder_path = os.path.join(base_path, "out", "invertidos")
    combined_audio_folder = os.path.join(base_path, "out", "audios")
    final_video_folder = os.path.join(base_path, "out", "videos")
    overlay_video = os.path.join(base_path, "in", "overlays", "overlay.mp4")

    folders_to_check = [
        audio_folder_path,
        image_folder_path,
        video_folder_path,
        inverted_folder_path,
        combined_audio_folder,
        final_video_folder,
        os.path.dirname(overlay_video)
    ]

    for folder in folders_to_check:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Folder created: {folder}")
        else:
            print(f"Folder already exists: {folder}")


def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Error al borrar {file_path}. {str(e)}')

def apply_fade(audio_path, fade_duration):
    audio = AudioSegment.from_file(audio_path)
    if fade_duration > 0:
        faded_audio = audio.fade_in(fade_duration).fade_out(fade_duration)
    else:
        faded_audio = audio
    return faded_audio

def concatenate_audios(audio_segments):
    concatenated_audio = AudioSegment.empty()
    for segment in audio_segments:
        concatenated_audio += segment
    return concatenated_audio

def invert_video_render(video_path, output_path, fps):
    command = ['ffmpeg', '-r', f'{fps}', '-i', video_path, '-vf', 'reverse', output_path]
    subprocess.run(command, check=True)

def randomize_names():
    words = [
        "Chill", "Vibes", "Lofi", "Study", "Relaxing", "Beats", "Calm", "Nights",
        "Smooth", "Sounds", "Peaceful", "Moments", "Dreamy", "Tunes", "Zen",
        "Serene", "Melodies", "Chillhop", "Essentials", "Relaxation", "Station",
        "Mellow", "Moods", "Tranquil", "Tracks", "Lounge", "Easy", "Listening",
        "Soothing", "Rhythms", "Groove", "Gentle", "Quiet", "Hours", "Sunset",
        "Morning", "Dreams", "Midnight", "Jazz", "Soft", "Comforting", "Daydream",
        "Cozy", "Ambiance", "Downtime", "Grooves", "Serenity", "Now", "Flow",
        "Chillwave", "Hazy", "Days", "Laid-Back", "Sleepy", "Time", "Reflective",
        "Ambient", "Warm", "Breeze", "Cloudy", "Mornings", "Starlit", "Skies",
        "Ocean", "Waves", "Raindrops", "Fireplace", "Crackle", "Moonlit", "Walks",
        "Urban", "Acoustic", "Café", "Music", "Vintage", "Lazy", "Afternoons",
        "Dusk", "Till", "Dawn", "Twilight", "Echoes", "Ethereal", "Whispers",
        "Dreamscape", "Celestial", "Harmonies", "Hypnotic", "Soulful", "Journeys",
        "Misty", "Mountains", "Lush", "Valleys", "Echoing", "Chords", "Mystic",
        "Sunsets", "Silent", "Reverie", "Harmony", "Floating", "Calmness",
        "Solitude", "Reflections", "Serenade", "Distant", "Glowing", "Aura",
        "Warmth", "Whisper", "Meditation", "Bliss", "Drifting", "Placid",
        "Gentleness", "Enchanted", "Sublime", "Echos", "Glimmers", "Wander",
        "Hushed", "Zenith", "Quietude", "Ease", "Stillness", "Embers", "Eden",
        "Nostalgia", "Restful", "Melancholy", "Pastel", "Gleam", "Lullaby",
        "Heavenly", "Peace", "Blissful", "Comfy", "Cinematic", "Drift",
        "Timeless", "Embrace", "Radiant", "Daylight", "Tranquility", "Softly",
        "Pensive", "Harmonious", "Shimmer", "Calming", "Reverberate", "Haze",
        "Blissfully", "Moonbeam", "Whispering", "Gleaming", "Radiating", "Serenely",
        "Faint", "Celestial", "Enveloping", "Tender", "Melodic", "Euphoric", "Hush",
        "Rest", "Glimmering", "Lull", "Soothingly", "Reflective"
    ]

    part1 = ' '.join(random.sample(words, 2))
    part2 = ' '.join(random.sample(words, 2))
    title = f"{part1} - {part2}"
    return title

def add_emoticon_to_title(title, position='start'):

    emoticons = [
    '🎵', '🎶', '🎧', '🎼', '🎤', '📻', '💿', '🎹',
    '🛋️', '☕', '🌙', '🌌', '🌟', '💤', '🎚️',
    '🧘', '🎷', '🎺', '🎻', '📚', '✨', '🖼️',
    '🖌️', '🌿', '🌵'
    ]

    # Selecciona un emoticón al azar
    emoticon = random.choice(emoticons)
    
    # Agrega el emoticón al principio o al final del título
    if position == 'start':
        new_title = f"{emoticon} {title}"
    elif position == 'end':
        new_title = f"{title} {emoticon}"
    else:
        raise ValueError("Position must be 'start' or 'end'.")
    
    return new_title

def get_audio_duration(file_path):
    audio = AudioSegment.from_file(file_path)
    return len(audio) / 1000  # duración en segundos

# Render Images


def render_massive_images(audio_folder_path, image_folder_path, combined_audio_folder, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, use_api_DEZGO, api_prompt, api_execution, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores):

    if use_audios_drive:
        print("Downloading audios from drive")
        service = authenticate()
        list_and_download_audio_files(service)
    else:
        print("Audios will not be downloaded from drive, those from the 'audios' folder will be used")

    if use_api_DEZGO:
        print(f"Creating {api_execution} images with the API, please wait...")
        create_images_ia(api_key, url_api, api_endpoint, api_prompt, api_width, api_height, api_sampler, api_model_id, api_negative_prompt, api_seed, api_format, api_guidance, api_transparent_background, api_execution, image_folder_path)

    image_files = [f for f in os.listdir(image_folder_path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    audio_files = [f for f in os.listdir(audio_folder_path) if f.endswith(('.mp3', '.wav', '.aac'))]

    if randomize_audios:
        random.shuffle(audio_files)

    num_images = len(image_files)
    num_audios = len(audio_files)

    if num_images == 0 or num_audios == 0:
        print("Not enough images or audios to create videos.")
        return

    audios_per_image = num_audios // num_images
    remaining_audios = num_audios % num_images

    audio_index = 0

    for i, image_file in enumerate(image_files):
        print(f"Processing image {i + 1}/{num_images}: {image_file}")

        audio_segments = []
        time_marker = timedelta(0)
        timestamps = []

        for _ in range(audios_per_image):
            if audio_index < num_audios:
                audio_file = audio_files[audio_index]
                audio_path = os.path.join(audio_folder_path, audio_file)
                faded_audio = apply_fade(audio_path, fade_duration)
                audio_segments.append(faded_audio)

                # Add timestamp entry
                duration = get_audio_duration(audio_path)
                timestamps.append(f"{time_marker} - {audio_file}")
                time_marker += timedelta(seconds=duration)

                audio_index += 1

        if i < remaining_audios:
            audio_file = audio_files[audio_index]
            audio_path = os.path.join(audio_folder_path, audio_file)
            faded_audio = apply_fade(audio_path, fade_duration)
            audio_segments.append(faded_audio)

            # Add timestamp entry
            duration = get_audio_duration(audio_path)
            timestamps.append(f"{time_marker} - {audio_file}")
            time_marker += timedelta(seconds=duration)

            audio_index += 1

        combined_audio = concatenate_audios(audio_segments)
        combined_audio_path = os.path.join(combined_audio_folder, f'combined_audio_{i + 1}.mp3')
        combined_audio.export(combined_audio_path, format="mp3")

        image_path = os.path.join(image_folder_path, image_file)

        if randomize_name:
            output_name = randomize_names() + '.mp4'
        else:
            output_name = os.path.splitext(image_file)[0] + '.mp4'
        
        output = os.path.join(final_video_folder, output_name)
        print(f"Creating video {i + 1}/{num_images} with image {image_file} and combined audio.")

        finaly_image_render(image_path, combined_audio_path, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, preset, pix_fmt, encoder, quality_level, aspect_ratio, cores, upload_files_youtube)

        # Save timestamps to a .txt file
        txt_path = os.path.join(final_video_folder, os.path.splitext(output_name)[0] + '.txt')
        with open(txt_path, 'w') as txt_file:
            for line in timestamps:
                txt_file.write(line + '\n')

        print(f"Timestamp file created: {txt_path}")

    if upload_files_drive:
        print(f"Uploading files to drive in folder {FOLDER_UPLOAD_NAME}")
        service = authenticate()
        folder_id_upload = get_or_create_folder(service, FOLDER_UPLOAD_NAME)
        upload_files(service, folder_id_upload, FOLDER_UPLOAD_PATH)
    else:
        print("Files will not be uploaded, but they are saved in the 'out/videos' folder")

def render_image(audio_folder_path, image_folder_path, combined_audio_folder, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, use_api_DEZGO, api_prompt, api_execution, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores):

    if use_audios_drive:
        print("Downloading audios from drive")
        service = authenticate()
        list_and_download_audio_files(service)
    else:
        print("Audios will not be downloaded from drive, those from the 'audios' folder will be used")

    files = os.listdir(audio_folder_path)
    audio_files = [f for f in files if f.endswith(('.mp3', '.wav', '.aac'))]

    if randomize_audios:
        random.shuffle(audio_files)

    if len(audio_files) == 0:
        print("Not enough audios to create videos.")
        return

    audio_segments = []
    time_marker = timedelta(0)
    timestamps = []

    for audio_file in audio_files:
        audio_path = os.path.join(audio_folder_path, audio_file)
        faded_audio = apply_fade(audio_path, fade_duration)
        audio_segments.append(faded_audio)

        # Add timestamp entry
        duration = get_audio_duration(audio_path)
        timestamps.append(f"{time_marker} - {audio_file}")
        time_marker += timedelta(seconds=duration)

    if len(audio_segments) == 0:
        print("Not enough audios to create videos.")
        return

    combined_audio = concatenate_audios(audio_segments)
    combined_audio_path = os.path.join(combined_audio_folder, 'combined_audio.mp3')
    combined_audio.export(combined_audio_path, format="mp3")

    if use_api_DEZGO:
        print("Creating images with API")
        create_images_ia(api_key, url_api, api_endpoint, api_prompt, api_width, api_height, api_sampler, api_model_id, api_negative_prompt, api_seed, api_format, api_guidance, api_transparent_background, 1, image_folder_path)

    image_file = [f for f in os.listdir(image_folder_path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))][0]
    if len(image_file) == 0:
        print("Not enough images to create videos.")
        return    
    image_path = os.path.join(image_folder_path, image_file)

    if randomize_name:
        output_name = randomize_names() + '.mp4'
    else:
        output_name = os.path.splitext(image_file)[0] + '.mp4'
    
    output = os.path.join(final_video_folder, output_name)

    finaly_image_render(image_path, combined_audio_path, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, preset, pix_fmt, encoder, quality_level, aspect_ratio, cores, upload_files_youtube)

    # Save timestamps to a .txt file
    txt_path = os.path.join(final_video_folder, os.path.splitext(output_name)[0] + '.txt')
    with open(txt_path, 'w') as txt_file:
        for line in timestamps:
            txt_file.write(line + '\n')
    
    print(f"Timestamp file created: {txt_path}")

    if upload_files_drive:
        print(f"Uploading files to drive in folder {FOLDER_UPLOAD_NAME}")
        service = authenticate()
        folder_id_upload = get_or_create_folder(service, FOLDER_UPLOAD_NAME)
        upload_files(service, folder_id_upload, FOLDER_UPLOAD_PATH)
    else:
        print("Files will not be uploaded, but they are saved in the 'out/videos' folder")

def finaly_image_render(image_folder_path, combined_audio_folder, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, preset, pix_fmt, encoder, quality_level, aspect_ratio, cores, upload_files_youtube):
 
        start_time = time.time()

        if not output.endswith('.mp4'):
            output += '.mp4'
        
        width, height = map(int, resolution.split('x'))
        audio_duration = AudioSegment.from_file(combined_audio_folder).duration_seconds
        
        temp = os.path.join(os.path.dirname(output), 'temp.mp4')

        if overlay:

            command_step1 = [
                'ffmpeg', '-y', '-loop', '1', '-i', image_folder_path, '-i', overlay_video,
                '-filter_complex', f'[0:v]scale={width}:{height}[bg];[1:v]scale={width}:{height},format=gbrp,colorchannelmixer=aa={opacity}[ovr];[bg][ovr]blend=all_mode={blend_mode}:shortest=1[v]',
                '-map', '[v]',
                '-c:v', encoder, '-preset', preset, '-pix_fmt', pix_fmt, '-b:v', video_bitrate,
                '-r', f'{fps}', '-threads', str(cores), '-aspect', aspect_ratio, temp
            ]

            command_step2 = [
                'ffmpeg', '-y', '-stream_loop', '-1', '-i', temp, '-i', combined_audio_folder,
                '-c:v', encoder, '-preset', preset, '-pix_fmt', pix_fmt, '-b:v', video_bitrate,
                '-c:a', 'aac', '-b:a', audio_quality,
                '-r', f'{fps}', '-threads', str(cores), '-aspect', aspect_ratio, '-shortest', output
            ]

            subprocess.run(command_step1, check=True)
            subprocess.run(command_step2, check=True)

            os.remove(temp)
        else:
            command = [
                'ffmpeg', '-loop', '1', '-i', image_folder_path, '-i', combined_audio_folder,
                '-c:v', encoder, '-preset', preset, '-pix_fmt', pix_fmt, '-b:v', video_bitrate,
                '-c:a', 'aac', '-b:a', audio_quality, '-shortest', 
                '-vf', f'scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1',
                '-r', f'{fps}', '-threads', str(cores), '-aspect', aspect_ratio, output
            ] 
            subprocess.run(command, check=True)

        if upload_files_youtube:
            print(f"Uploading file to YouTube in folder {FOLDER_UPLOAD_NAME}")
            youtube_service = authenticate_youtube()
            video_file_path = output
            title = f"Video {output}"
            upload_video_to_youtube(youtube_service, video_file_path, title, description, tags, category_id, privacy_status)
        else:
            print("Files will not be uploaded to YouTube, but they are saved in the 'out/videos' folder")

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Video {output} successfully created.")
        print(f"Rendering time: {elapsed_time / 60:.2f} minutes")

# Render Videos
def render_massive_videos(audio_folder_path, video_folder_path, combined_audio_folder, inverted_folder_path, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, invert_video, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores):
      
    if use_audios_drive:
        print("Downloading audios from drive")
        service = authenticate()
        list_and_download_audio_files(service)
    else:
        print("Audios will not be downloaded from drive, those from the 'audios' folder will be used")

    video_files = [f for f in os.listdir(video_folder_path) if f.endswith(('.mp4', '.avi', '.mkv'))]
    audio_files = [f for f in os.listdir(audio_folder_path) if f.endswith(('.mp3', '.wav', '.aac'))]

    if randomize_audios:
        random.shuffle(audio_files)

    num_videos = len(video_files)
    num_audios = len(audio_files)

    if num_videos == 0 or num_audios == 0:
        print("Not enough videos or audios to create videos.")
        return

    audios_per_video = num_audios // num_videos
    remaining_audios = num_audios % num_videos

    audio_index = 0

    for i, video_file in enumerate(video_files):
        print(f"Processing video {i + 1}/{num_videos}: {video_file}")

        audio_segments = []
        time_marker = timedelta(0)
        timestamps = []

        for _ in range(audios_per_video):
            if audio_index < num_audios:
                audio_path = os.path.join(audio_folder_path, audio_files[audio_index])
                faded_audio = apply_fade(audio_path, fade_duration)
                audio_segments.append(faded_audio)

                # Add timestamp entry
                duration = get_audio_duration(audio_path)
                timestamps.append(f"{time_marker} - {audio_files[audio_index]}")
                time_marker += timedelta(seconds=duration)

                audio_index += 1

        if i < remaining_audios:
            audio_path = os.path.join(audio_folder_path, audio_files[audio_index])
            faded_audio = apply_fade(audio_path, fade_duration)
            audio_segments.append(faded_audio)

            # Add timestamp entry
            duration = get_audio_duration(audio_path)
            timestamps.append(f"{time_marker} - {audio_files[audio_index]}")
            time_marker += timedelta(seconds=duration)

            audio_index += 1

        combined_audio = concatenate_audios(audio_segments)
        combined_audio_path = os.path.join(combined_audio_folder, f'combined_audio_{i + 1}.mp3')
        combined_audio.export(combined_audio_path, format="mp3")

        video_path = os.path.join(video_folder_path, video_file)

        if randomize_name:
            output_name = randomize_names() + '.mp4'
        else:
            output_name = os.path.splitext(video_file)[0] + '.mp4'

        output = os.path.join(final_video_folder, output_name)

        if invert_video:
            inverted_video = os.path.join(inverted_folder_path, f'inverted_video_{i + 1}.mp4')
            invert_video_render(video_path, inverted_video, fps)
            combined_video_path = os.path.join(inverted_folder_path, f'combined_video_{i + 1}.mp4')
            command = ['ffmpeg', '-r', f'{fps}', '-i', video_path, '-r', f'{fps}', '-i', inverted_video, '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0[out]', '-map', '[out]', combined_video_path]
            subprocess.run(command, check=True)
            finaly_video_render(combined_video_path, combined_audio_path, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, encoder, preset, pix_fmt, aspect_ratio, cores, upload_files_youtube)
        else:
            finaly_video_render(video_path, combined_audio_path, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, encoder, preset, pix_fmt, aspect_ratio, cores, upload_files_youtube)

        # Save timestamps to a .txt file
        txt_path = os.path.join(final_video_folder, os.path.splitext(output_name)[0] + '.txt')
        with open(txt_path, 'w') as txt_file:
            for line in timestamps:
                txt_file.write(line + '\n')

        print(f"Timestamp file created: {txt_path}")

    if upload_files_drive:
         print(f"Uploading files to drive in folder {FOLDER_UPLOAD_NAME}")
         service = authenticate()
         folder_id_upload = get_or_create_folder(service, FOLDER_UPLOAD_NAME)
         upload_files(service, folder_id_upload, FOLDER_UPLOAD_PATH)
    else:
        print("Files will not be uploaded, but they are saved in the 'out/videos' folder")

def render_video(video_folder_path, audio_folder_path, combined_audio_folder, inverted_folder_path, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, invert_video, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores):
    
    if use_audios_drive:
        print("Downloading audios from drive")
        service = authenticate()
        list_and_download_audio_files(service)
    else:
        print("Audios will not be downloaded from drive, those from the 'audios' folder will be used")

    files = os.listdir(audio_folder_path)
    audio_files = [f for f in files if f.endswith(('.mp3', '.wav', '.aac'))]

    if randomize_audios:
        random.shuffle(audio_files)

    if not audio_files:
        print("No audio files found.")
        return

    audio_segments = []
    time_marker = timedelta(0)
    timestamps = []

    for audio_file in audio_files:
        audio_path = os.path.join(audio_folder_path, audio_file)
        faded_audio = apply_fade(audio_path, fade_duration)
        audio_segments.append(faded_audio)

        # Add timestamp entry
        duration = get_audio_duration(audio_path)
        timestamps.append(f"{time_marker} - {audio_file}")
        time_marker += timedelta(seconds=duration)

    if not audio_segments:
        print("Audio files could not be processed.")
        return
    
    combined_audio = concatenate_audios(audio_segments)
    combined_audio_path = os.path.join(combined_audio_folder, 'combined_audio.mp3')
    combined_audio.export(combined_audio_path, format="mp3")

    video_file = [f for f in os.listdir(video_folder_path) if f.endswith(('.mp4', '.avi', '.mkv'))][0]
    if not video_file:
        print("No video files found.")
        return
    video_path = os.path.join(video_folder_path, video_file)

    if randomize_name:
        output_name = randomize_names() + '.mp4'
    else:
        output_name = os.path.splitext(video_file)[0] + '.mp4'

    output = os.path.join(final_video_folder, output_name)

    if invert_video:
        inverted_video = os.path.join(inverted_folder_path, 'inverted_video.mp4')
        invert_video_render(video_path, inverted_video, fps)
        combined_video_path = os.path.join(inverted_folder_path, 'combined_video.mp4')
        command = ['ffmpeg', '-r', f'{fps}', '-i', video_path, '-r', f'{fps}', '-i', inverted_video, '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0[out]', '-map', '[out]', combined_video_path]
        subprocess.run(command, check=True)
        finaly_video_render(combined_video_path, combined_audio_path, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, encoder, preset, pix_fmt, aspect_ratio, cores, upload_files_youtube)
    else:
        finaly_video_render(video_path, combined_audio_path, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, encoder, preset, pix_fmt, aspect_ratio, cores, upload_files_youtube)

    # Save timestamps to a .txt file
    txt_path = os.path.join(final_video_folder, os.path.splitext(output_name)[0] + '.txt')
    with open(txt_path, 'w') as txt_file:
        for line in timestamps:
            txt_file.write(line + '\n')

    print(f"Timestamp file created: {txt_path}")

    if upload_files_drive:
         print(f"Uploading files to drive in folder {FOLDER_UPLOAD_NAME}")
         service = authenticate()
         folder_id_upload = get_or_create_folder(service, FOLDER_UPLOAD_NAME)
         upload_files(service, folder_id_upload, FOLDER_UPLOAD_PATH)
    else:
        print("Files will not be uploaded, but they are saved in the 'out/videos' folder")

def finaly_video_render(video_folder_path, combined_audio_folder, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, encoder, preset, pix_fmt, aspect_ratio, cores, upload_files_youtube):
 
        start_time = time.time()

        if not output.endswith('.mp4'):
            output += '.mp4'
        
        width, height = map(int, resolution.split('x'))

        temp = os.path.join(os.path.dirname(output), 'temp.mp4')
        
        if overlay:
            if not overlay_video.endswith('.mp4'):
                overlay_video += '.mp4'

            command_step1 = [
                    'ffmpeg', '-y', '-i', video_folder_path, '-i', overlay_video,
                    '-filter_complex', f'''
                        [0:v]scale={width}:{height}[bg];
                        [1:v]scale={width}:{height},format=gbrp,colorchannelmixer=aa={opacity}[ovr];
                        [bg][ovr]blend=all_mode={blend_mode}:shortest=1,scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1[v];
                    ''',
                    '-map', '[v]',
                    '-map', '0:a?',
                    '-c:v', encoder, '-preset', preset, '-pix_fmt', pix_fmt, '-b:v', video_bitrate,
                    '-c:a', 'aac', '-b:a', audio_quality, '-shortest',
                    '-r', f'{fps}', '-threads', str(cores), '-aspect', aspect_ratio, temp
                ]

            command_step2 = [
                'ffmpeg', '-y', '-stream_loop', '-1', '-i', temp, '-i', combined_audio_folder,
                '-filter_complex', f'''
                    [0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1[v];
                ''',
                '-map', '[v]',
                '-map', '1:a?',
                '-c:v', encoder, '-preset', preset, '-pix_fmt', pix_fmt, '-b:v', video_bitrate,
                '-c:a', 'aac', '-b:a', audio_quality, '-shortest',
                '-r', f'{fps}', '-threads', str(cores), '-aspect', aspect_ratio, output
            ]

            subprocess.run(command_step1, check=True)
            subprocess.run(command_step2, check=True)

            os.remove(temp)
        else:
            command = [
                    'ffmpeg', '-stream_loop', '-1', '-r', f'{fps}', '-i', video_folder_path, '-i', combined_audio_folder,
                    '-c:v', encoder, '-preset', preset, '-pix_fmt', pix_fmt, '-b:v', video_bitrate,
                    '-c:a', 'aac', '-b:a', audio_quality, '-shortest', '-vf',f'scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1', 
                    '-r', f'{fps}', '-threads', str(cores), '-aspect', aspect_ratio, output
            ]  
            subprocess.run(command, check=True)
            
        if upload_files_youtube:
            print(f"Uploading file to YouTube in folder {FOLDER_UPLOAD_NAME}")
            youtube_service = authenticate_youtube()
            video_file_path = output
            title = f"{output}"
            upload_video_to_youtube(youtube_service, video_file_path, title, description, tags, category_id, privacy_status)
        else:
            print("Files will not be uploaded to YouTube, but they are saved in the 'out/videos' folder")
            

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Video {output} successfully created.")
        print(f"Rendering time: {elapsed_time / 60:.2f} minutes")

################## FUNCIONES SUNO ################
def create_audios_from_api(suno_prompt, suno_execution, instrumental, suno_wait_audio, audio_folder_path, base_api_suno_url):

    for i in range(int(suno_execution)):
        print(f"{Fore.CYAN}Creando audio (x2) {i+1} de {suno_execution}{Style.RESET_ALL}")
        
        data = generate_audio_by_prompt({
            "prompt": suno_prompt,
            "make_instrumental": instrumental,
            "wait_audio": suno_wait_audio
        }, base_api_suno_url)

        ids = f"{data[0]['id']},{data[1]['id']}"
        print(f"{Fore.YELLOW}IDs generados: {ids}{Style.RESET_ALL}")

        # Esperar hasta que los audios estén listos
        for _ in range(60):
            data = get_audio_information(ids)
            if data[0]["status"] == 'complete' and data[1]["status"] == 'complete':
                audio_url_1 = data[0]['audio_url']
                audio_url_2 = data[1]['audio_url']
                
                # Extraer nombres de archivos desde las URLs
                file_name_1 = f"{data[0]['title']}_1.mp3"
                file_name_2 = f"{data[1]['title']}_2.mp3"
                
                unique_file_name_1 = ensure_unique_file_name(file_name_1, audio_folder_path)
                unique_file_name_2 = ensure_unique_file_name(file_name_2, audio_folder_path)

                print(f"{Fore.GREEN}{data[0]['id']} ==> {audio_url_1}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}{data[1]['id']} ==> {audio_url_2}{Style.RESET_ALL}")

                # Descargar los audios
                download_audio(audio_url_1, unique_file_name_1, audio_folder_path)
                download_audio(audio_url_2, unique_file_name_2, audio_folder_path)

                # Verificar duración de los audios
                duration_1 = get_audio_duration(os.path.join(audio_folder_path, unique_file_name_1))
                duration_2 = get_audio_duration(os.path.join(audio_folder_path, unique_file_name_2))

                if duration_1 < 60:
                    print(f"{Fore.RED}Duración de {unique_file_name_1} demasiado corta, se eliminará{Style.RESET_ALL}")
                    os.remove(os.path.join(audio_folder_path, unique_file_name_1))
                if duration_2 < 60:
                    print(f"{Fore.RED}Duración de {unique_file_name_2} demasiado corta, se eliminará{Style.RESET_ALL}")
                    os.remove(os.path.join(audio_folder_path, unique_file_name_2))

                break
            else:
                print(f"{Fore.MAGENTA}Esperando que los audios estén completos...{Style.RESET_ALL}")
                time.sleep(20)

def ensure_unique_file_name(file_name, folder_path):

    base_name, extension = os.path.splitext(file_name)
    counter = 1
    unique_file_name = file_name
    
    while os.path.exists(os.path.join(folder_path, unique_file_name)):
        unique_file_name = f"{base_name}_{counter}{extension}"
        counter += 1
        
    return unique_file_name

def custom_generate_audio(payload):
    url = f"{base_api_suno_url}/api/custom_generate"
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    return response.json()

def extend_audio(payload):
    url = f"{base_api_suno_url}/api/extend_audio"
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    return response.json()

def generate_audio_by_prompt(payload, base_api_suno_url):
    url = f"{base_api_suno_url}/api/generate"
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        try:
            data = response.json()
            return data
        except requests.exceptions.JSONDecodeError:
            print("Error: The response is not a valid JSON.")
            print(f"Server response: {response.text}")
    else:
        print(f"Request error: {response.status_code}")
        print(f"Server response: {response.text}")

    return response.json()

def get_audio_information(audio_ids):
    url = f"{base_api_suno_url}/api/get?ids={audio_ids}"
    response = requests.get(url)
    return response.json()

def get_quota_information():
    url = f"{base_api_suno_url}/api/get_limit"
    response = requests.get(url)
    return response.json()

def get_clip(clip_id):
    url = f"{base_api_suno_url}/api/clip?id={clip_id}"
    response = requests.get(url)
    return response.json()

def generate_whole_song(clip_id):
    payload = {"clip_id": clip_id}
    url = f"{base_api_suno_url}/api/concat"
    response = requests.post(url, json=payload)
    return response.json()

def download_audio(audio_url, file_name, save_path):
    try:
        file_path = f"{save_path}/{file_name}"
        
        response = requests.get(audio_url)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Audio downloaded and saved as {file_name}")
        else:
            print(f"Error downloading audio from {audio_url}: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while downloading the audio: {e}")


################## FUNCIONES Dezgo ################
def create_images_ia(api_key, url_api, api_endpoint, api_prompt, api_width, api_height, api_sampler, api_model_id, api_negative_prompt, api_seed, api_format, api_guidance, api_transparent_background, api_execution, image_folder_path, retry_delay=5, max_retries=3):
    url = f"{url_api}/{api_endpoint}"
    headers = {
        'X-Dezgo-Key': api_key
    }

    # Split the prompts by the "|" separator
    prompts = api_prompt.split('|')
    num_prompts = len(prompts)
    
    # Calculate how many images per prompt
    images_per_prompt = int(api_execution) // num_prompts
    remaining_images = int(api_execution) % num_prompts  # To distribute the remaining images

    image_count = 0
    for idx, prompt in enumerate(prompts):
        # Adjust the number of images for the first prompts if there are remaining images
        num_images = images_per_prompt + (1 if idx < remaining_images else 0)

        # Clean the prompt to use it as part of the file name
        clean_prompt = re.sub(r'[^\w\s-]', '', prompt).strip().replace(' ', '_')  # Removes invalid characters and replaces spaces with underscores
        
        # Limit the length of the filename to 20 characters
        clean_prompt = clean_prompt[:20]

        for i in range(num_images):
            success = False
            attempts = 0
            files = {
                'prompt': (None, prompt),
                'width': (None, str(api_width)),
                'height': (None, str(api_height)),
                #'sampler': (None, api_sampler),
                #'model': (None, api_model_id),
                #'negative_prompt': (None, api_negative_prompt),
                'steps': 5,
                'seed': (None, api_seed),
                'format': (None, api_format),
                #'guidance': (None, str(api_guidance)),
                'transparent_background': (None, str(api_transparent_background).lower())
            }

            while not success and attempts < max_retries:
                try:
                    response = requests.post(url, headers=headers, files=files)
                    response.raise_for_status()  # Raise an exception for 4xx or 5xx codes

                    if response.status_code == 200:
                        image_count += 1
                        print(f'Successful request for prompt {idx+1}, image {image_count}')
                        # Save the image in image_folder_path with the original prompt name
                        image_filename = f'{clean_prompt}_{i+1}.jpg'
                        image_path = os.path.join(image_folder_path, image_filename)
                        with open(image_path, 'wb') as f:
                            f.write(response.content)
                            print(f'Image saved at: {image_path}')
                        success = True
                    else:
                        print(f'Error in the request for image {image_count}: {response.status_code}, {response.text}')
                        attempts += 1
                        if attempts < max_retries:
                            print(f'Retrying in {retry_delay} seconds...')
                            time.sleep(retry_delay)
                except requests.exceptions.RequestException as e:
                    print(f'Request error: {e}')
                    attempts += 1
                    if attempts < max_retries:
                        print(f'Retrying in {retry_delay} seconds...')
                        time.sleep(retry_delay)

            if not success:
                print(f'Could not complete the request for image {image_count} after {max_retries} attempts.')


################## DRIVE FUNCTIONS ################

def authenticate():
    # Load client credentials from the credentials file

    creds = None

    # Load credentials from the service account JSON file
    if os.path.exists(SERVICE_ACCOUNT_SECRET_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_SECRET_FILE, scopes=SCOPES
        )

    # If the credentials have expired, refresh them
    if not creds.valid:
        creds.refresh(Request())

    # Build the Google Drive API service
    service = build('drive', 'v3', credentials=creds)
    return service

def list_and_download_audio_files(service):
    try:
        # Get the 'audio' folder ID or create it if it doesn't exist
        folder_id = get_or_create_folder(service, FOLDER_NAME)
        if not folder_id:
            print(f'Could not get or create the folder "{FOLDER_NAME}" on your Google Drive.')
            return

        print(f'ID of the "audio" folder: {folder_id}')

        # Build the query string for the MIME types
        mime_query = ' or '.join([f"mimeType='{mime}'" for mime in AUDIO_MIME_TYPES])

        # Get the list of audio files in the 'audio' folder
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false and ({mime_query})",
            fields="nextPageToken, files(name, id)").execute()
        items = results.get('files', [])

        print(f'Audio files found in the "{FOLDER_NAME}" folder:')
        for item in items:
            print(f"- {item['name']}")

        if not items:
            print("No audio files found in the folder.")
            return

        # Ask the user which files to download
        download_choice = 'all'

        if download_choice.lower() == 'all':
            # Download all audio files from the folder
            for item in items:
                download_success = download_file(service, item['name'], item['id'], DOWNLOAD_PATH)
                if download_success:
                    print(f'File "{item["name"]}" successfully downloaded.')
                else:
                    print(f'Error downloading the file "{item["name"]}".')

    except HttpError as error:
        print(f'HTTP Error: {error}')
    except Exception as e:
        print(f'General error: {e}')

def get_or_create_folder(service, folder_name):
    # Function to get the folder ID by name or create it if it doesn't exist
    folder_id = None

    # Check if the folder exists
    results = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id)").execute()
    items = results.get('files', [])
    if items:
        folder_id = items[0]['id']
    else:
        # Create the folder if it doesn't exist
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')

    return folder_id

def download_file(service, file_name, file_id, download_path):
    # Function to download a file by name from a specific folder
    try:
        request = service.files().get_media(fileId=file_id)
        file_stream = request.execute()

        # Save the downloaded file to the specified local directory
        download_file_path = os.path.join(download_path, file_name)
        with open(download_file_path, 'wb') as f:
            f.write(file_stream)

        return True  # Indicate that the download was successful

    except HttpError as error:
        print(f'Error downloading the file "{file_name}": {error}')
        return False  # Indicate that the download failed
    except Exception as e:
        print(f'General error downloading the file "{file_name}": {e}')
        return False  # Indicate that the download failed

def upload_files(service, folder_id, local_folder_path):
    # Function to upload all files from a local folder to a Google Drive folder
    for file_name in os.listdir(local_folder_path):
        file_path = os.path.join(local_folder_path, file_name)
        if os.path.isfile(file_path):
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            media = MediaFileUpload(file_path, resumable=True)
            try:
                file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                print(f'File "{file_name}" successfully uploaded with ID "{file.get("id")}".')
            except HttpError as error:
                print(f'Error uploading the file "{file_name}": {error}')


################## FUNCIONES YOUTUBE ################

def authenticate_youtube():
    creds = None
    if os.path.exists('token-yt.json'):
        creds = Credentials.from_authorized_user_file('token-yt.json', YOUTUBE_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                YOUTUBE_CLIENT_SECRET_FILE, YOUTUBE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token-yt.json', 'w') as token:
            token.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)

def authenticate_youtube_partner():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_SECRET_FILE, scopes=SCOPES_PARTNER)
    
    youtube_partner_service = build('youtubePartner', 'v1', credentials=credentials)
    return youtube_partner_service


def get_content_owner_id(access_token):
    url = "https://www.googleapis.com/youtube/partner/v1/contentOwners?fetchMine=true"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    content_owners = response.json()
    return content_owners['items'][0]['id']  # Suponiendo que tienes solo un propietario de contenido

def create_asset(access_token, content_owner_id, video_id):
    url = "https://www.googleapis.com/youtube/partner/v1/assets"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    body = {
        "contentOwner": content_owner_id,
        "type": "VIDEO",
        "videoId": video_id
    }
    response = requests.post(url, json=body, headers=headers)
    response.raise_for_status()
    asset = response.json()
    return asset['id']

def set_ownership(access_token, asset_id, content_owner_id):
    url = f"https://www.googleapis.com/youtube/partner/v1/assets/{asset_id}/ownership"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    body = {
        "contentOwner": content_owner_id
    }
    response = requests.post(url, json=body, headers=headers)
    response.raise_for_status()
    return response.json()

def claim_video(access_token, asset_id, content_owner_id, policy_id):
    url = f"https://www.googleapis.com/youtube/partner/v1/assets/{asset_id}/claims"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    body = {
        "contentOwner": content_owner_id,
        "policy": {
            "id": policy_id
        }
    }
    response = requests.post(url, json=body, headers=headers)
    response.raise_for_status()
    return response.json()

def monetize_video(access_token, video_id):
    content_owner_id = get_content_owner_id(access_token)
    asset_id = create_asset(access_token, content_owner_id, video_id)
    set_ownership(access_token, asset_id, content_owner_id)
    
    # Obtén el POLICY_ID de una consulta previa o usa uno existente
    policy_id = "YOUR_POLICY_ID"
    claim_video(access_token, asset_id, content_owner_id, policy_id)

def upload_video_to_youtube(youtube_service, video_file_path, title, description, tags, category_id, privacy_status):
    try:
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False  # Ajusta según sea necesario
            }
        }

        media_body = MediaFileUpload(video_file_path, chunksize=1024*1024, resumable=True)

        request = youtube_service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media_body
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                sys.stdout.write(f'\rSubida {int(status.progress() * 100)}% completada.')
                sys.stdout.flush()
                time.sleep(0.1)  # Agrega un pequeño retraso para evitar que el bucle se ejecute demasiado rápido

        if response:
            print(f'\nVideo subido exitosamente. ID: {response["id"]}')
            monetize_video(authenticate_youtube_partner(), response["id"])

    except HttpError as error:
        print(f'\nError al subir el video a YouTube: {error}')
    except Exception as e:
        print(f'\nError general al subir el video a YouTube: {e}')

def enable_monetization(youtube_service, video_id):
    try:
        body = {
            'monetizationDetails': {
                'access': 'allowed'  # Este es un ejemplo, ajusta según sea necesario
            }
        }

        request = youtube_service.videos().update(
            part="monetizationDetails",
            body={
                'id': video_id,
                'monetizationDetails': body['monetizationDetails']
            }
        )

        response = request.execute()
        print(f'Monetización habilitada para el video. ID: {response["id"]}')
    except HttpError as error:
        print(f'Error al habilitar la monetización en YouTube: {error}')
    except Exception as e:
        print(f'Error general al habilitar la monetización en YouTube: {e}')

def upload_all_videos_to_youtube(folder_path):
    print(f"Subiendo archivos a YouTube desde la carpeta {folder_path}")
    youtube_service = authenticate_youtube()  # Función para autenticarse con YouTube API

    for filename in os.listdir(folder_path):
        if filename.endswith('.mp4'):  # Asegurarse de subir solo archivos de video
            video_file_path = os.path.join(folder_path, filename)
            title = f"{filename}"  # Título del video basado en el nombre del archivo
            upload_video_to_youtube(youtube_service, video_file_path, title, description, tags, category_id, privacy_status)

##################### EXECUTE THE PROGRAM ###################
def loading_effect():
    for _ in range(5):
        for char in '|/-\\':
            sys.stdout.write(f'\r{Fore.YELLOW}Loading {char} {Style.RESET_ALL}')
            sys.stdout.flush()
            time.sleep(0.2)
    
    # Clear the loading line after finishing
    sys.stdout.write('\r' + ' ' * 20 + '\r')
    sys.stdout.flush()

def ask_user_option(prompt, options): 
    converted_options = ['Yes' if opt is True else 'No' if opt is False else opt for opt in options]

    while True:
        print(f"{Fore.BLUE}## {prompt} ##{Style.RESET_ALL}")  
        for i, option in enumerate(converted_options, 1):
            print(f'{Fore.GREEN}{i} - {option}{Style.RESET_ALL}') 
        
        try:
            choice = int(input(f'{Fore.YELLOW}Select a number: {Style.RESET_ALL}')) 
            
            if 1 <= choice <= len(converted_options):
                return options[choice - 1]  # Return the original value, not the converted one
            else:
                print(f"{Fore.RED}Please choose a number between 1 and {len(converted_options)}.{Style.RESET_ALL}")  

        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")  


def start_render():

    # General variables and functions
    fps = 30 # 25 or 30
    resolution = "1920x1080" # '1920x1080','1280x720','854x480','640x360'
    aspect_ratio = "16:9" # '16:9','4:3','1:1'
    video_bitrate = "3000k" # '1000k','2000k','3000k','4000k'

    audio_quality = "192k" # '128k','192k','320k'
    fade_duration = 3000 # in milliseconds
    randomize_audios = True # True or False
    randomize_name = True # True or False

    overlay = True # True or False
    overlay_name = "dust_final.mp4" # 'particles.mp4', 'vhs.mp4', 'vhs-lines.mp4', 'dust.mp4', 'dust_final.mp4'
    opacity = 1 # between 0 and 1
    blend_mode = "addition" # 'addition','multiply','screen','overlay','darken','lighten','color-dodge','color-burn','hard-light','soft-light','difference','exclusion','hue','saturation','color','luminosity'

    invert_video = True # True or False

    encoder = "h264_qsv" # 'libx264','h264_nvenc','h264_qsv','h264_amf','h264_videotoolbox'
    quality_level = 3  # 1 is the best quality, 3 is the lowest quality

    # API to create images
    use_api_DEZGO = False # True or False
    api_prompt = "magic Landscape tokyo realistic 4k high quality" # API prompt
    api_execution = 19 # number of images to create with the API

    # Suno configuration variables
    use_suno_api = False
    suno_prompt = "Lofi ambient chill"
    instrumental = True
    suno_wait_audio = True
    suno_execution = 22

    use_audios_drive = False # True or False
    upload_files_drive = False # True or False
    upload_files_youtube = False # True or False

    # Preset mapping according to quality
    quality_presets = {
        1: 'veryslow',  # Best quality
        2: 'medium',    # Medium quality
        3: 'veryfast'   # Low quality
    }

    # Encoder settings with presets according to quality
    encoder_settings = {
        'libx264': {'pix_fmt': 'yuv420p','presets': quality_presets},
        'h264_nvenc': {'pix_fmt': 'yuv420p','presets': {1: 'p1', 2: 'p4', 3: 'p7'}},
        'h264_qsv': {'pix_fmt': 'nv12','presets': quality_presets},
        'h264_amf': {'pix_fmt': 'nv12','presets': quality_presets},
        'h264_videotoolbox': {'pix_fmt': 'nv12','presets': {1: 'slow', 2: 'medium', 3: 'fast'}},
        'hevc_nvenc': {'pix_fmt': 'yuv420p','presets': {1: 'p1', 2: 'p4', 3: 'p7'}},
        'hevc_qsv': {'pix_fmt': 'nv12','presets': quality_presets},
        'hevc_amf': {'pix_fmt': 'nv12','presets': quality_presets},
        'hevc_videotoolbox': {'pix_fmt': 'nv12','presets': {1: 'slow', 2: 'medium', 3: 'fast'}},
        'vp9_nvenc': {'pix_fmt': 'yuv420p','presets': {1: 'p1', 2: 'p4', 3: 'p7'}},
        'vp9_qsv': {'pix_fmt': 'nv12','presets': quality_presets},
        'vp9_amf': {'pix_fmt': 'nv12','presets': quality_presets},
        'vp9_videotoolbox': {'pix_fmt': 'nv12','presets': {1: 'slow', 2: 'medium', 3: 'fast'}},
        'av1_nvenc': {'pix_fmt': 'yuv420p','presets': {1: 'p1', 2: 'p4', 3: 'p7'}},
        'av1_qsv': {'pix_fmt': 'nv12','presets': quality_presets},
        'av1_amf': {'pix_fmt': 'nv12','presets': quality_presets},
        'av1_videotoolbox': {'pix_fmt': 'nv12','presets': {1: 'slow', 2: 'medium', 3: 'fast'}},
        'libx265': {'pix_fmt': 'yuv420p','presets': {1: 'veryslow', 2: 'medium', 3: 'fast'}}
    }
    preset = encoder_settings[encoder]['presets'][quality_level]
    pix_fmt = encoder_settings[encoder]['pix_fmt']

    # Define paths for specific folders
    audio_folder_path = os.path.join(base_path, "in", "audios")
    image_folder_path = os.path.join(base_path, "in", "imagenes")
    video_folder_path = os.path.join(base_path, "in", "videos")
    inverted_folder_path = os.path.join(base_path, "out", "invertidos")
    combined_audio_folder = os.path.join(base_path, "out", "audios")
    final_video_folder = os.path.join(base_path, "out", "videos")
    overlay_video = os.path.join(base_path, "in", "overlays", overlay_name)

    print('\n')
    print('Welcome to render module v1.0.0')
    loading_effect()
    print('\n')

    # Checking input and output folders
    print('Checking folders...')
    create_folders(base_path)
    print('\n')


    render_type = ask_user_option('What type of render do you want?', ['render_image', 'render_video', 'render_image_massive', 'render_video_massive', 'upload_youtube', 'generate_images', 'generate_audios'])
    print('\n')

    if render_type != "upload_youtube":
        delete_folders = ask_user_option('It is necessary to delete the contents of the OUT folders (even if they are empty), do we continue?', [True, False])

        if delete_folders:
            print('Deleting folders...')
            clear_folder(final_video_folder)
            clear_folder(combined_audio_folder)
            clear_folder(inverted_folder_path)
        else:
            print('The contents of the OUT folders will not be deleted')
            print('Please make sure the OUT folders are clean before rendering')
            print('Process canceled')
            return

    print('\n')

    delete_folders = ask_user_option('Do you want to delete the contents of the IN folders (if you select yes, we will ask you which folders to delete)?', [True, False])

    if delete_folders:
        print('Deleting folders...')
        if ask_user_option('Do you want to delete the contents of the images folder (recommended if using DEZGO)?', [True, False]):
            clear_folder(image_folder_path)
        if ask_user_option('Do you want to delete the contents of the audio folder (recommended if using SUNO)?', [True, False]):
            clear_folder(audio_folder_path)
        if ask_user_option('Do you want to delete the contents of the videos folder?', [True, False]):
            clear_folder(video_folder_path)
    print('\n')

    if render_type not in {'upload_youtube', 'generate_images', 'generate_audios'}:
        config = ask_user_option('Do you want to configure the render now?', [True, False])


        if config:
            # Questions for general variables
            fps = int(ask_user_option('Select FPS:', [20, 25, 30, 60]))
            resolution = ask_user_option('Select resolution:', ['1920x1080', '1280x720', '854x480', '640x360'])
            aspect_ratio = ask_user_option('Select aspect ratio:', ['16:9', '4:3', '1:1'])
            video_bitrate = ask_user_option('Select video bitrate:', ['1000k', '2000k', '3000k', '4000k'])
            encoder = ask_user_option('Select video encoder:', ['libx264', 'h264_nvenc', 'h264_qsv', 'h264_amf', 'h264_videotoolbox'])
            quality_level = int(ask_user_option('Select quality level 3 (high), 2 (medium), or 1 (low):', [1, 2, 3]))
            audio_quality = ask_user_option('Select audio quality:', ['128k', '192k', '320k'])
            fade_duration = int(input('Enter fade duration in milliseconds (e.g. 3000):'))
            randomize_audios = ask_user_option('Do you want to randomize the audios?', [True, False]) 
            randomize_name = ask_user_option('Do you want to randomize the names?', [True, False]) 
            
            overlay = ask_user_option('Do you want to use an overlay?', [True, False])
            if overlay:
                overlay_name = ask_user_option('Enter the overlay name:', ['snow.mp4', 'particles.mp4', 'vhs.mp4', 'vhs-lines.mp4', 'dust.mp4', 'dust-final.mp4'])
                opacity = float(input('Enter the overlay opacity (0 to 1): '))
                blend_mode = ask_user_option('Select the blend mode:', ['addition', 'multiply', 'screen', 'overlay', 'darken', 'lighten', 'hard-light', 'soft-light'])

            if render_type == 'render_video' or render_type == 'render_video_massive':
                invert_video = ask_user_option('Do you want to invert the video?', [True, False])

            if render_type == 'render_image_massive' or render_type == 'render_image':
                use_api_DEZGO = ask_user_option('Use the DEZGO API to create images?', [True, False])
                if use_api_DEZGO:
                    api_prompt = input('Enter the API prompt (use | to separate different prompts): ')
                    api_execution = int(input('Enter the number of images to create with the API: '))

            use_suno_api = ask_user_option('Use the Suno API to create audios?', [True, False])
            if use_suno_api:
                suno_prompt = input('Enter the Suno API prompt:')
                suno_execution = int(input('Enter the number of audios to create with the Suno API (Generates 2 audios per execution): '))

    def print_variable_state(name, value):
        # Prints the state of a boolean variable in red or green
        state_color = Fore.GREEN if value else Fore.RED  # Green if True, Red if False
        print(f'{name}: {state_color}{value}{Style.RESET_ALL}')

    def show_initial_data():
        print("\n" + "="*50)
        print("CHECK BEFORE STARTING:")
        print("="*50)

        # General render data
        print(f'Render type: {render_type}')
        print(f'Resolution: {resolution}')
        print(f'FPS: {fps}')
        print(f'Video bitrate: {video_bitrate}')
        print(f'Audio quality: {audio_quality}')
        print(f'Fade duration: {fade_duration}')
        print(f'Encoder: {encoder}')
        print(f'Quality level: {quality_level}')
        print(f'Aspect ratio: {aspect_ratio}')

        # API usage
        print("\nAPI USAGE:")
        if render_type in ['render_image_massive', 'render_image']:
            print_variable_state('Using DEZGO image API', use_api_DEZGO)
            if use_api_DEZGO:
                print(f'Number of images to generate: {api_execution}')
                print(f'Image prompt (use | to separate different prompts): {api_prompt}')

        print_variable_state('Using Suno API', use_suno_api)
        if use_suno_api:
            print(f'Suno API prompt: {suno_prompt}')
            print(f'Number of audios to generate (x2): {suno_execution * 2}')

        # Other settings
        print("\nOTHER SETTINGS:")
        print_variable_state('Using random names', randomize_name)
        print_variable_state('Using random audios', randomize_audios)

        if render_type in ['render_video', 'render_video_massive']:
            print_variable_state('Invert video', invert_video)

        if overlay:
            print_variable_state('Using overlay', overlay)
            print(f'Overlay name: {overlay_name}')
            print(f'Overlay opacity: {opacity}')
            print(f'Blend mode: {blend_mode}')

        print("\n" + "="*50)
        print("CHECK BEFORE STARTING")
        print("="*50)

    # Main flow logic
    if render_type == "upload_youtube":
        print(f'You selected to upload all final videos to YouTube')
    elif render_type == "generate_images":
        print(f'You selected to generate images')
        use_api_DEZGO = True
        api_prompt = input('Enter the API prompt (use | to separate different prompts): ')
        api_execution = int(input('Enter the number of images to create with the API: '))
        print("\n" + "="*50)
        print("CHECK BEFORE STARTING")
        print("="*50)
        print_variable_state('Using DEZGO image API', use_api_DEZGO)
        print(f'Image prompt: {api_prompt}')
        print(f'API image executions: {api_execution}')
        print("\n" + "="*50)
        print("CHECK BEFORE STARTING")
        print("="*50)
    elif render_type == "generate_audios":
        print(f'You selected to generate audios')
        use_suno_api = True
        suno_prompt = input('Enter the Suno API prompt: ')
        suno_execution = int(input('Enter the number of audios to create with the Suno API (Generates 2 audios per execution): '))
        print("\n" + "="*50)
        print("CHECK BEFORE STARTING")
        print("="*50)
        print_variable_state('Using Suno API', use_suno_api)
        print(f'Suno API prompt: {suno_prompt}')
        print(f'Total Suno API executions (x2): {suno_execution * 2}')
        print("\n" + "="*50)
        print("CHECK BEFORE STARTING")
        print("="*50)

    print('\n')
    if not "generate_audios" in render_type and not "generate_images" in render_type and not "upload_youtube" in render_type:
        show_initial_data()

    init = ask_user_option('Do you want to start the render?', ['yes, start', 'no, stop'])

    if init.lower() == "yes, start":
        loading_effect()
        print('\n')

        if render_type == "generate_audios":

            create_audios_from_api(suno_prompt, suno_execution, instrumental, suno_wait_audio, audio_folder_path, base_api_suno_url)
        elif render_type == "generate_images":

            create_images_ia(api_key, url_api, api_endpoint, api_prompt, api_width, api_height, api_sampler, api_model_id, api_negative_prompt, api_seed, api_format, api_guidance, api_transparent_background, api_execution, image_folder_path)
        elif render_type == "upload_youtube":

            upload_all_videos_to_youtube(final_video_folder)
        elif render_type == "render_video":
            if use_suno_api:
                create_audios_from_api(suno_prompt, suno_execution, instrumental, suno_wait_audio, audio_folder_path, base_api_suno_url)            
            render_video(video_folder_path, audio_folder_path, combined_audio_folder, inverted_folder_path, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, invert_video, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores)
        elif render_type == "render_image":
            if use_suno_api:
                create_audios_from_api(suno_prompt, suno_execution, instrumental, suno_wait_audio, audio_folder_path, base_api_suno_url)
            render_image(audio_folder_path, image_folder_path, combined_audio_folder, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, use_api_DEZGO, api_prompt, api_execution, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores)
        elif render_type == "render_image_massive":
            if use_suno_api:
                create_audios_from_api(suno_prompt, suno_execution, instrumental, suno_wait_audio, audio_folder_path, base_api_suno_url)
            render_massive_images(audio_folder_path, image_folder_path, combined_audio_folder, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, use_api_DEZGO, api_prompt, api_execution, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores)
        elif render_type == "render_video_massive":
            if use_suno_api:
                create_audios_from_api(suno_prompt, suno_execution, instrumental, suno_wait_audio, audio_folder_path, base_api_suno_url)
            render_massive_videos(audio_folder_path, video_folder_path, combined_audio_folder, inverted_folder_path, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, invert_video, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores)

    else:
        print("Process canceled.")
        return

    print("Process finished.")
    return

start_render()
