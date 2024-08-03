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
api_key = "DEZGO-820FA4D500D9754DDE2A6E6B9E3DD5BBF28160EA20654895CE9A0F89E30406F7E1AA4C62"
api_endpoint = "text2image_sdxl_lightning"
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
            print(f"Carpeta creada: {folder}")
        else:
            print(f"Carpeta ya existe: {folder}")

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
        print("Descargando audios de drive")
        service =authenticate()
        list_and_download_audio_files(service)
    else:
        print("No se descargaran audios de drive, se usaran los de la carpeta 'audios'")

    if use_api_DEZGO:
        print(f"Creando {api_execution} imagenes con la api, por favor espere...")
        create_images_ia(api_key, url_api, api_endpoint, api_prompt, api_width, api_height, api_sampler, api_model_id, api_negative_prompt, api_seed, api_format, api_guidance, api_transparent_background, api_execution, image_folder_path)

    image_files = [f for f in os.listdir(image_folder_path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    audio_files = [f for f in os.listdir(audio_folder_path) if f.endswith(('.mp3', '.wav', '.aac'))]

    if randomize_audios:
        random.shuffle(audio_files)

    num_images = len(image_files)
    num_audios = len(audio_files)

    if num_images == 0 or num_audios == 0:
        print("No hay suficientes imágenes o audios para crear videos.")
        return

    audios_per_image = num_audios // num_images
    remaining_audios = num_audios % num_images

    audio_index = 0

    for i, image_file in enumerate(image_files):
        print(f"Procesando imagen {i + 1}/{num_images}: {image_file}")

        audio_segments = []

        for _ in range(audios_per_image):
            if audio_index < num_audios:
                audio_file = audio_files[audio_index]
                audio_path = os.path.join(audio_folder_path, audio_file)
                faded_audio = apply_fade(audio_path, fade_duration)
                audio_segments.append(faded_audio)
                audio_index += 1

        if i < remaining_audios:
            audio_file = audio_files[audio_index]
            audio_path = os.path.join(audio_folder_path, audio_file)
            faded_audio = apply_fade(audio_path, fade_duration)
            audio_segments.append(faded_audio)
            audio_index += 1

        combined_audio = concatenate_audios(audio_segments)
        combined_audio_path = os.path.join(combined_audio_folder, f'combined_audio_{i + 1}.mp3')
        combined_audio.export(combined_audio_path, format="mp3")

        image_path = os.path.join(image_folder_path, image_file)

        if randomize_name:
            output = os.path.join(final_video_folder, randomize_names() + '.mp4')
        else:
            output = os.path.join(final_video_folder, os.path.splitext(image_file)[0] + '.mp4')

        print(f"Creando video {i + 1}/{num_images} con la imagen {image_file} y audio combinado.")

        finaly_image_render(image_path, combined_audio_path, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, preset, pix_fmt, encoder, quality_level, aspect_ratio, cores, upload_files_youtube)

    if upload_files_drive:
         print(f"Subiendo archivos al drive en carpeta {FOLDER_UPLOAD_NAME}")
         service = authenticate()
         folder_id_upload = get_or_create_folder(service, FOLDER_UPLOAD_NAME)
         upload_files(service, folder_id_upload, FOLDER_UPLOAD_PATH)
    else:
        print("No se subiran los archivos, pero si se guardaron en la carpeta 'out/videos'")
        
def render_image(audio_folder_path, image_folder_path, combined_audio_folder, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, use_api_DEZGO, api_prompt, api_execution, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores):

    if use_audios_drive:
        print("Descargando audios de drive")
        service =authenticate()
        list_and_download_audio_files(service)
    else:
        print("No se descargaran audios de drive, se usaran los de la carpeta 'audios'")

    files = os.listdir(audio_folder_path)
    audio_files = [f for f in files if f.endswith(('.mp3', '.wav', '.aac'))]

    if randomize_audios:
        random.shuffle(audio_files)

    if len(audio_files) == 0:
        print("No hay suficientes audios para crear videos.")
        return

    audio_segments = []
    for audio_file in audio_files:
        audio_path = os.path.join(audio_folder_path, audio_file)
        faded_audio = apply_fade(audio_path, fade_duration)
        audio_segments.append(faded_audio)

    if len(audio_segments) == 0:
        print("No hay suficientes audios para crear videos.")
        return

    combined_audio = concatenate_audios(audio_segments)
    combined_audio_path = os.path.join(combined_audio_folder, 'combined_audio.mp3')
    combined_audio.export(combined_audio_path, format="mp3")

    if use_api_DEZGO:
        print("Creando imagenes con api")
        create_images_ia(api_key, url_api, api_endpoint, api_prompt, api_width, api_height, api_sampler, api_model_id, api_negative_prompt, api_seed, api_format, api_guidance, api_transparent_background, 1, image_folder_path)

    image_file = [f for f in os.listdir(image_folder_path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))][0]
    if len(image_file) == 0:
        print("No hay suficientes imágenes para crear videos.")
        return    
    image_path = os.path.join(image_folder_path, image_file)

    if randomize_name:
        output = os.path.join(final_video_folder, randomize_names() + '.mp4')
    else:
        output = os.path.join(final_video_folder, os.path.splitext(image_file)[0] + '.mp4')

    finaly_image_render(image_path, combined_audio_path, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, preset, pix_fmt, encoder, quality_level, aspect_ratio, cores, upload_files_youtube)
    
    if upload_files_drive:
         print(f"Subiendo archivos al drive en carpeta {FOLDER_UPLOAD_NAME}")
         service = authenticate()
         folder_id_upload = get_or_create_folder(service, FOLDER_UPLOAD_NAME)
         upload_files(service, folder_id_upload, FOLDER_UPLOAD_PATH)
    else:
        print("No se subiran los archivos, pero si se guardaron en la carpeta 'out/videos'")


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
            print(f"Subiendo archivo a youtube en carpeta {FOLDER_UPLOAD_NAME}")
            youtube_service = authenticate_youtube()
            video_file_path = output
            title = f"Video {output}"
            upload_video_to_youtube(youtube_service, video_file_path, title, description, tags, category_id, privacy_status)
        else:
            print("No se subiran los archivos a youtube, pero si se guardaron en la carpeta 'out/videos'")

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Video {output} creado con éxito.")
        print(f"Tiempo de renderizado: {elapsed_time / 60:.2f} minutos")

# Render Videos

def render_massive_videos(audio_folder_path, video_folder_path, combined_audio_folder, inverted_folder_path, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, invert_video, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores):
      
    if use_audios_drive:
        print("Descargando audios de drive")
        service =authenticate()
        list_and_download_audio_files(service)
    else:
        print("No se descargaran audios de drive, se usaran los de la carpeta 'audios'")

    video_files = [f for f in os.listdir(video_folder_path) if f.endswith(('.mp4', '.avi', '.mkv'))]
    audio_files = [f for f in os.listdir(audio_folder_path) if f.endswith(('.mp3', '.wav', '.aac'))]

    if randomize_audios:
        random.shuffle(audio_files)

    num_videos = len(video_files)
    num_audios = len(audio_files)

    if num_videos == 0 or num_audios == 0:
        print("No hay suficientes videos o audios para crear videos.")
        return

    audios_per_video = num_audios // num_videos
    remaining_audios = num_audios % num_videos

    audio_index = 0

    for i, video_file in enumerate(video_files):
        print(f"Procesando video {i + 1}/{num_videos}: {video_file}")

        audio_segments = []

        for _ in range(audios_per_video):
            if audio_index < num_audios:
                audio_path = os.path.join(audio_folder_path, audio_files[audio_index])
                faded_audio = apply_fade(audio_path, fade_duration)
                audio_segments.append(faded_audio)
                audio_index += 1

        if i < remaining_audios:
            audio_path = os.path.join(audio_folder_path, audio_files[audio_index])
            faded_audio = apply_fade(audio_path, fade_duration)
            audio_segments.append(faded_audio)
            audio_index += 1

        combined_audio = concatenate_audios(audio_segments)
        combined_audio_path = os.path.join(combined_audio_folder, f'combined_audio_{i + 1}.mp3')
        combined_audio.export(combined_audio_path, format="mp3")

        video_path = os.path.join(video_folder_path, video_file)

        if randomize_name:
            output = os.path.join(final_video_folder, randomize_names() + '.mp4')
        else:
            output = os.path.join(final_video_folder, os.path.splitext(video_file)[0] + '.mp4')

        if invert_video:
            inverted_video = os.path.join(inverted_folder_path, f'inverted_video_{i + 1}.mp4')
            invert_video_render(video_path, inverted_video, fps)
            combined_video_path = os.path.join(inverted_folder_path, f'combined_video_{i + 1}.mp4')
            command = ['ffmpeg', '-r', f'{fps}', '-i', video_path, '-r', f'{fps}', '-i', inverted_video, '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0[out]', '-map', '[out]', combined_video_path]
            subprocess.run(command, check=True)
            finaly_video_render(combined_video_path, combined_audio_path, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, encoder, preset, pix_fmt, aspect_ratio, cores, upload_files_youtube)
        else:
            finaly_video_render(video_path, combined_audio_path, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, encoder, preset, pix_fmt, aspect_ratio, cores, upload_files_youtube)


    if upload_files_drive:
         print(f"Subiendo archivos al drive en carpeta {FOLDER_UPLOAD_NAME}")
         service = authenticate()
         folder_id_upload = get_or_create_folder(service, FOLDER_UPLOAD_NAME)
         upload_files(service, folder_id_upload, FOLDER_UPLOAD_PATH)
    else:
        print("No se subiran los archivos, pero si se guardaron en la carpeta 'out/videos'")

def render_video(video_folder_path, audio_folder_path, combined_audio_folder, inverted_folder_path, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, invert_video, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores):
    
    if use_audios_drive:
        print("Descargando audios de drive")
        service =authenticate()
        list_and_download_audio_files(service)
    else:
        print("No se descargaran audios de drive, se usaran los de la carpeta 'audios'")

    files = os.listdir(audio_folder_path)
    audio_files = [f for f in files if f.endswith(('.mp3', '.wav', '.aac'))]

    if randomize_audios:
        random.shuffle(audio_files)

    if not audio_files:
        print("No se encontraron archivos de audio.")
        return

    audio_segments = []
    for audio_file in audio_files:
        audio_path = os.path.join(audio_folder_path, audio_file)
        faded_audio = apply_fade(audio_path, fade_duration)
        audio_segments.append(faded_audio)

    if not audio_segments:
        print("No se pudieron procesar los archivos de audio.")
        return
    
    combined_audio = concatenate_audios(audio_segments)
    combined_audio_path = os.path.join(combined_audio_folder, 'combined_audio.mp3')
    combined_audio.export(combined_audio_path, format="mp3")

    # buscamos un video en la carpeta sin importar el nombre de archivo que termine en .mp4, .avi o .mkv
    video_file = [f for f in os.listdir(video_folder_path) if f.endswith(('.mp4', '.avi', '.mkv'))][0]
    if not video_file:
        print("No se encontraron archivos de video.")
        return
    video_path = os.path.join(video_folder_path, video_file)

    if randomize_name:
        output = os.path.join(final_video_folder, randomize_names() + '.mp4')
    else:
        output = os.path.join(final_video_folder, os.path.splitext(video_file)[0] + '.mp4')

    if invert_video:
        inverted_video = os.path.join(inverted_folder_path, 'inverted_video.mp4')
        invert_video_render(video_path, inverted_video, fps)
        print(f"Video invertido: {inverted_video}")
        combined_video_path = os.path.join(inverted_folder_path, 'combined_video.mp4')
        command = ['ffmpeg', '-r', f'{fps}', '-i', video_path, '-r', f'{fps}', '-i', inverted_video, '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0[out]', '-map', '[out]', combined_video_path]
        subprocess.run(command, check=True)
        print(f"Video combinado: {combined_video_path}")
        finaly_video_render(combined_video_path, combined_audio_path, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, encoder, preset, pix_fmt, aspect_ratio, cores, upload_files_youtube)
    else:
        finaly_video_render(video_path, combined_audio_path, output, resolution, fps, video_bitrate, audio_quality, overlay_video, overlay, opacity, blend_mode, encoder, preset, pix_fmt, aspect_ratio, cores, upload_files_youtube)

    if upload_files_drive:
         print(f"Subiendo archivos al drive en carpeta {FOLDER_UPLOAD_NAME}")
         service = authenticate()
         folder_id_upload = get_or_create_folder(service, FOLDER_UPLOAD_NAME)
         upload_files(service, folder_id_upload, FOLDER_UPLOAD_PATH)
    else:
        print("No se subiran los archivos, pero si se guardaron en la carpeta 'out/videos'")


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
            print(f"Subiendo archivo a youtube en carpeta {FOLDER_UPLOAD_NAME}")
            youtube_service = authenticate_youtube()
            video_file_path = output
            title = f"{output}"
            upload_video_to_youtube(youtube_service, video_file_path, title, description, tags, category_id, privacy_status)
        else:
            print("No se subiran los archivos a youtube, pero si se guardaron en la carpeta 'out/videos'")
            

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Video {output} creado con éxito.")
        print(f"Tiempo de renderizado: {elapsed_time / 60:.2f} minutos")

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

def generate_audio_by_prompt(payload,base_api_suno_url):
    url = f"{base_api_suno_url}/api/generate"
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
            try:
                data = response.json()
                return data
            except requests.exceptions.JSONDecodeError:
                print("Error: La respuesta no es un JSON válido.")
                print(f"Respuesta del servidor: {response.text}")
    else:
            print(f"Error en la solicitud: {response.status_code}")
            print(f"Respuesta del servidor: {response.text}")

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
            print(f"Audio descargado y guardado como {file_name}")
        else:
            print(f"Error al descargar el audio desde {audio_url}: {response.status_code}")
    except Exception as e:
        print(f"Se produjo un error al descargar el audio: {e}")


################## FUNCIONES Dezgo ################

# funcion para generar imagenes masivas con dezgo mediante su api
def create_images_ia(api_key, url_api, api_endpoint, api_prompt, api_width, api_height, api_sampler, api_model_id, api_negative_prompt, api_seed, api_format, api_guidance, api_transparent_background, api_execution, image_folder_path, retry_delay=5, max_retries=3):
    url = f"{url_api}/{api_endpoint}"
    headers = {
        'X-Dezgo-Key': api_key
    }
    files = {
        'prompt': (None, api_prompt),
        'width': (None, str(api_width)),
        'height': (None, str(api_height)),
        'sampler': (None, api_sampler),
        'model': (None, api_model_id),
        'negative_prompt': (None, api_negative_prompt),
        'seed': (None, api_seed),
        'format': (None, api_format),
        'guidance': (None, str(api_guidance)),
        'transparent_background': (None, str(api_transparent_background).lower())
    }

    for i in range(int(api_execution)):
        success = False
        attempts = 0
        while not success and attempts < max_retries:
            try:
                response = requests.post(url, headers=headers, files=files)
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

                if response.status_code == 200:
                    print(f'Solicitud {i+1} exitosa')
                    # Guardar la imagen en image_folder_path
                    image_path = os.path.join(image_folder_path, f'image_{i+1}.jpg')
                    with open(image_path, 'wb') as f:
                        f.write(response.content)
                        print(f'Imagen guardada en: {image_path}')
                    success = True
                else:
                    print(f'Error en la solicitud {i+1}: {response.status_code}, {response.text}')
                    attempts += 1
                    if attempts < max_retries:
                        print(f'Reintentando en {retry_delay} segundos...')
                        time.sleep(retry_delay)
            except requests.exceptions.RequestException as e:
                print(f'Error en la solicitud: {e}')
                attempts += 1
                if attempts < max_retries:
                    print(f'Reintentando en {retry_delay} segundos...')
                    time.sleep(retry_delay)

        if not success:
            print(f'No se pudo completar la solicitud {i+1} después de {max_retries} intentos.')

################## FUNCIONES DRIVE ################

def authenticate():
    # Cargar las credenciales de cliente desde el archivo de credenciales

    creds = None

    # Cargar las credenciales desde el archivo JSON del servicio
    if os.path.exists(SERVICE_ACCOUNT_SECRET_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_SECRET_FILE, scopes=SCOPES
        )

    # Si las credenciales han expirado, refrescarlas
    if not creds.valid:
        creds.refresh(Request())

    # Construir el servicio de Google Drive API
    service = build('drive', 'v3', credentials=creds)
    return service

def list_and_download_audio_files(service):
    try:
        # Obtener el ID de la carpeta 'audio' o crearla si no existe
        folder_id = get_or_create_folder(service, FOLDER_NAME)
        if not folder_id:
            print(f'No se pudo obtener ni crear la carpeta "{FOLDER_NAME}" en tu Google Drive.')
            return

        print(f'ID de la carpeta "audio": {folder_id}')

        # Construir la cadena de consulta para los tipos MIME
        mime_query = ' or '.join([f"mimeType='{mime}'" for mime in AUDIO_MIME_TYPES])

        # Obtener la lista de archivos de audio en la carpeta 'audio'
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false and ({mime_query})",
            fields="nextPageToken, files(name, id)").execute()
        items = results.get('files', [])

        print(f'Archivos de audio encontrados en la carpeta "{FOLDER_NAME}":')
        for item in items:
            print(f"- {item['name']}")

        if not items:
            print("No se encontraron archivos de audio en la carpeta.")
            return

        # Preguntar al usuario qué archivos desea descargar
        download_choice = 'all'

        if download_choice.lower() == 'all':
            # Descargar todos los archivos de audio de la carpeta
            for item in items:
                download_success = download_file(service, item['name'], item['id'], DOWNLOAD_PATH)
                if download_success:
                    print(f'Archivo "{item["name"]}" descargado exitosamente.')
                else:
                    print(f'Error al descargar el archivo "{item["name"]}".')

    except HttpError as error:
        print(f'Error de HTTP: {error}')
    except Exception as e:
        print(f'Error general: {e}')

def get_or_create_folder(service, folder_name):
    # Función para obtener el ID de la carpeta por nombre o crearla si no existe
    folder_id = None

    # Verificar si la carpeta existe
    results = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id)").execute()
    items = results.get('files', [])
    if items:
        folder_id = items[0]['id']
    else:
        # Crear la carpeta si no existe
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')

    return folder_id

def download_file(service, file_name, file_id, download_path):
    # Función para descargar un archivo por nombre desde una carpeta específica
    try:
        request = service.files().get_media(fileId=file_id)
        file_stream = request.execute()

        # Guardar el archivo descargado en el directorio local especificado
        download_file_path = os.path.join(download_path, file_name)
        with open(download_file_path, 'wb') as f:
            f.write(file_stream)

        return True  # Indicar que la descarga fue exitosa

    except HttpError as error:
        print(f'Error al descargar el archivo "{file_name}": {error}')
        return False  # Indicar que la descarga falló
    except Exception as e:
        print(f'Error general al descargar el archivo "{file_name}": {e}')
        return False  # Indicar que la descarga falló

def upload_files(service, folder_id, local_folder_path):
    # Función para subir todos los archivos de una carpeta local a una carpeta de Google Drive
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
                print(f'Archivo "{file_name}" subido exitosamente con ID "{file.get("id")}".')
            except HttpError as error:
                print(f'Error al subir el archivo "{file_name}": {error}')

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


##################### EJECUTAMOS EL PROGRAMA ###################
def loading_effect():
    for _ in range(5):
        for char in '|/-\\':
            sys.stdout.write(f'\r{Fore.YELLOW}Cargando {char} {Style.RESET_ALL}')
            sys.stdout.flush()
            time.sleep(0.2)
    
    # Limpiar la línea de carga después de terminar
    sys.stdout.write('\r' + ' ' * 20 + '\r')
    sys.stdout.flush()

def ask_user_option(prompt, options): 
    converted_options = ['Sí' if opt is True else 'No' if opt is False else opt for opt in options]

    while True:
        print(f"{Fore.BLUE}## {prompt} ##{Style.RESET_ALL}")  
        for i, option in enumerate(converted_options, 1):
            print(f'{Fore.GREEN}{i} - {option}{Style.RESET_ALL}') 
        
        try:
            choice = int(input(f'{Fore.YELLOW}Selecciona un número: {Style.RESET_ALL}')) 
            
            if 1 <= choice <= len(converted_options):
                return options[choice - 1]  # Devolver el valor original, no el convertido
            else:
                print(f"{Fore.RED}Por favor, elige un número entre 1 y {len(converted_options)}.{Style.RESET_ALL}")  

        except ValueError:
            print(f"{Fore.RED}Entrada no válida. Por favor, ingresa un número.{Style.RESET_ALL}")  


def start_render():

    # Variables y funciones generales
    fps = 30 # 25 o 30
    resolution = "1920x1080" # '1920x1080','1280x720','854x480','640x360'
    aspect_ratio = "16:9" # '16:9','4:3','1:1'
    video_bitrate = "3000k" # '1000k','2000k','3000k','4000k'

    audio_quality = "192k" # '128k','192k','320k'
    fade_duration = 3000 # en milisegundos
    randomize_audios = True # True o False
    randomize_name = True # True o False

    overlay = True # True o False
    overlay_name = "vhs-lines.mp4" # 'particles.mp4', 'vhs.mp4', 'vhs-lines.mp4', 'dust.mp4', 'dust-final.mp4'
    opacity = 1 # entre 0 y 1
    blend_mode = "addition" # 'addition','multiply','screen','overlay','darken','lighten','color-dodge','color-burn','hard-light','soft-light','difference','exclusion','hue','saturation','color','luminosity'

    invert_video = True # True o False

    encoder = "h264_qsv" # 'libx264','h264_nvenc','h264_qsv','h264_amf','h264_videotoolbox'
    quality_level = 3  # 1 es la mejor calidad, 3 es la más baja calidad

    # Api para crear imagenes
    use_api_DEZGO = False # True o False
    api_prompt = "Fantasy Forest Landscape realistic 4k high quality" # prompt de la api
    api_execution = 50 # cantidad de imagenes que se crearan con la api

    # Variables de configuración suno
    use_suno_api = False
    suno_prompt = "Lofi ambient chill"
    insrtumental = True
    suno_wait_audio = True
    suno_execution = 22

    use_audios_drive = False # True o False
    upload_files_drive = False # True o False
    upload_files_youtube = False # True o False

    # Mapeo de presets según la calidad
    quality_presets = {
        1: 'veryslow',  # Mejor calidad
        2: 'medium',    # Calidad media
        3: 'veryfast'   # Calidad baja
    }

    # Configuración del encoder con presets según la calidad
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

    # Definir rutas para las carpetas específicas
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

    # verificando carpetas in y out
    print('Checking folders...')
    create_folders(base_path)
    print('\n')

    render_type = ask_user_option('¿Que tipo de render quieres?', ['render_image', 'render_video', 'render_image_massive', 'render_video_massive', 'upload_youtube', 'generate_images', 'generate_audios'])
    print('\n')
    
    if render_type != "upload_youtube":
        delete_folders = ask_user_option('Es necesario eliminar el contenido de las carpetas OUT(aun que esten vacias), continuamos?', [True, False])

        if delete_folders:
            print('Deleting folders...')
            clear_folder(final_video_folder)
            clear_folder(combined_audio_folder)
            clear_folder(inverted_folder_path)
        else :
            print('No se eliminará el contenido de las carpetas OUT')
            print('Por favor asegurate de que el contenido de las carpetas OUT esté limpio antes de renderizar')
            print('Proceso cancelado')
            return

    print('\n')

    delete_folders = ask_user_option('¿Quieres eliminar el contenido de las carpetas IN (en caso de seleccionar si te preguntaremos que carpetas eliminar)?', [True, False])

    if delete_folders:
        print('Deleting folders...')
        if ask_user_option('¿Quieres eliminar el contenido de la carpeta imagenes (recomendado si usas DEZGO)?', [True, False]):
            clear_folder(image_folder_path)
        if ask_user_option('¿Quieres eliminar el contenido de la carpeta audios (recomendado si usas SUNO)?', [True, False]):
            clear_folder(audio_folder_path)
        if ask_user_option('¿Quieres eliminar el contenido de la carpeta videos?', [True, False]):
            clear_folder(video_folder_path)
    print('\n')

    if render_type not in {'upload_youtube', 'generate_images', 'generate_audios'}:
        config = ask_user_option('¿Quieres configurar el render a continuación?', [True, False])


        if config:
            # Preguntas para las variables generales
            fps = int(ask_user_option('Selecciona los FPS:', [20, 25, 30, 60]))
            resolution = ask_user_option('Selecciona la resolución:', ['1920x1080', '1280x720', '854x480', '640x360'])
            aspect_ratio = ask_user_option('Selecciona la relación de aspecto:', ['16:9', '4:3', '1:1'])
            video_bitrate = ask_user_option('Selecciona el bitrate del video:', ['1000k', '2000k', '3000k', '4000k'])
            encoder = ask_user_option('Selecciona el codificador de video:', ['libx264', 'h264_nvenc', 'h264_qsv', 'h264_amf', 'h264_videotoolbox'])
            quality_level = int(ask_user_option('Selecciona el nivel de calidad 3 (alta), 2 (media) o 1 (baja):', [1, 2, 3]))
            audio_quality = ask_user_option('Selecciona la calidad del audio:', ['128k', '192k', '320k'])
            fade_duration = int(input('Ingresa la duración del fade en milisegundos  (ej. 3000):'))
            randomize_audios = ask_user_option('¿Quieres randomizar los audios?', [True, False]) 
            randomize_name = ask_user_option('¿Quieres randomizar los nombres?', [True, False]) 
            
            overlay = ask_user_option('¿Quieres usar un overlay?', [True, False])
            if overlay:
                overlay_name = ask_user_option('Ingresa el nombre del overlay:', ['snow.mp4', 'particles.mp4', 'vhs.mp4', 'vhs-lines.mp4', 'dust.mp4', 'dust-final.mp4'])
                opacity = float(input('Ingresa la opacidad del overlay (0 a 1): '))
                blend_mode = ask_user_option('Selecciona el modo de mezcla:', ['addition', 'multiply', 'screen', 'overlay', 'darken', 'lighten', 'hard-light', 'soft-light'])

            if render_type == 'render_video' or render_type == 'render_video_massive':
                invert_video = ask_user_option('¿Quieres invertir el video?', [True, False])

            if render_type == 'render_image_massive' or render_type == 'render_image':
                use_api_DEZGO = ask_user_option('¿Usar la API DEZGO para crear imágenes?', [True, False])
                if use_api_DEZGO:
                    api_prompt = input('Ingresa el prompt de la API: ')
                    api_execution = int(input('Ingresa la cantidad de imágenes a crear con la API: '))

            use_suno_api = ask_user_option('¿Usar la API Suno para crear audios?', [True, False])
            if use_suno_api:
                suno_prompt = input('Ingresa el prompt de la API Suno: ')
                suno_execution = int(input('Ingresa la cantidad de audios a crear con la API Suno (Genera 2 audios por ejecución): '))

            # Variables adicionales
            #use_audios_drive = ask_user_option('¿Usar audios de Google Drive?', [True, False])
            #upload_files_drive = ask_user_option('¿Subir archivos a Google Drive?', [True, False]) 
            #upload_files_youtube = ask_user_option('¿Subir archivos a YouTube?', [True, False]) 

    def imprimir_estado_variable(nombre, valor):
        # Imprime el estado de una variable booleana en color rojo o verde
        estado_color = Fore.GREEN if valor else Fore.RED  # Verde si True, Rojo si False
        print(f'{nombre}: {estado_color}{valor}{Style.RESET_ALL}')

    def mostrar_datos_iniciales():
        print("\n" + "="*50)
        print("REVISAR ANTES DE COMENZAR:")
        print("="*50)

        # Datos generales del render
        print(f'Tipo de render: {render_type}')
        print(f'Resolución: {resolution}')
        print(f'FPS: {fps}')
        print(f'Video bitrate: {video_bitrate}')
        print(f'Audio quality: {audio_quality}')
        print(f'Duración del fade: {fade_duration}')
        print(f'Encoder: {encoder}')
        print(f'Calidad: {quality_level}')
        print(f'Aspect ratio: {aspect_ratio}')

        # Uso de APIs
        print("\nUSO DE APIs:")
        if render_type in ['render_image_massive', 'render_image']:
            imprimir_estado_variable('Usando API imágenes DEZGO', use_api_DEZGO)
            if use_api_DEZGO:
                print(f'Cantidad de imágenes a generar: {api_execution}')
                print(f'Prompt de imágenes: {api_prompt}')

        imprimir_estado_variable('Usando API Suno', use_suno_api)
        if use_suno_api:
            print(f'Prompt de API Suno: {suno_prompt}')
            print(f'Cantidad de audios a generar (x2): {suno_execution * 2}')

        # Otras configuraciones
        print("\nOTRAS CONFIGURACIONES:")
        imprimir_estado_variable('Usando nombres aleatorios', randomize_name)
        imprimir_estado_variable('Usando audios aleatorios', randomize_audios)

        if render_type in ['render_video', 'render_video_massive']:
            imprimir_estado_variable('Invertir video', invert_video)

        if overlay:
            imprimir_estado_variable('Usando overlay', overlay)
            print(f'Nombre del overlay: {overlay_name}')
            print(f'Opacidad del overlay: {opacity}')
            print(f'Modo de mezcla: {blend_mode}')

        print("\n" + "="*50)
        print("REVISAR ANTES DE COMENZAR")
        print("="*50)

    # Lógica del flujo principal
    if render_type == "upload_youtube":
        print(f'Seleccionaste subir todos los videos finales a YouTube')
    elif render_type == "generate_images":
        print(f'Seleccionaste generar imágenes')
        use_api_DEZGO = True
        api_prompt = input('Ingresa el prompt de la API: ')
        api_execution = int(input('Ingresa la cantidad de imágenes a crear con la API: '))
        print("\n" + "="*50)
        print("REVISAR ANTES DE COMENZAR")
        print("="*50)
        imprimir_estado_variable('Usando API imágenes DEZGO', use_api_DEZGO)
        print(f'Prompt de imágenes: {api_prompt}')
        print(f'Ejecuciones de API imágenes: {api_execution}')
        print("\n" + "="*50)
        print("REVISAR ANTES DE COMENZAR")
        print("="*50)
    elif render_type == "generate_audios":
        print(f'Seleccionaste generar audios')
        use_suno_api = True
        suno_prompt = input('Ingresa el prompt de la API Suno: ')
        suno_execution = int(input('Ingresa la cantidad de audios a crear con la API Suno (Genera 2 audios por ejecución): '))
        print("\n" + "="*50)
        print("REVISAR ANTES DE COMENZAR")
        print("="*50)
        imprimir_estado_variable('Usando API Suno', use_suno_api)
        print(f'Prompt de API Suno: {suno_prompt}')
        print(f'Ejecuciones de API Suno totales (X2): {suno_execution * 2}')
        print("\n" + "="*50)
        print("REVISAR ANTES DE COMENZAR")
        print("="*50)
        
    print('\n')
    if render_type != "generate_audios" or not "upload_youtube" or not "generate_images":
            mostrar_datos_iniciales()

    init = ask_user_option('¿Quieres iniciar el render?', ['si, iniciar', 'no, detener'])

    if init.lower() == "si, iniciar":
        loading_effect()
        print('\n')

        if render_type != "generate_audios" or not "upload_youtube" and use_suno_api:
            create_audios_from_api(suno_prompt, suno_execution, insrtumental, suno_wait_audio, audio_folder_path, base_api_suno_url)
            
        if render_type == "generate_audios":

            create_audios_from_api(suno_prompt, suno_execution, insrtumental, suno_wait_audio, audio_folder_path, base_api_suno_url)
        elif render_type == "generate_images":
    
            create_images_ia(api_key, url_api, api_endpoint, api_prompt, api_width, api_height, api_sampler, api_model_id, api_negative_prompt, api_seed, api_format, api_guidance, api_transparent_background, api_execution, image_folder_path)
        elif render_type == "upload_youtube":

            upload_all_videos_to_youtube(final_video_folder)
        elif render_type == "render_video":

            render_video(video_folder_path, audio_folder_path, combined_audio_folder, inverted_folder_path, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, invert_video, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores)
        elif render_type == "render_image":

            render_image(audio_folder_path, image_folder_path, combined_audio_folder, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, use_api_DEZGO, api_prompt, api_execution, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores)
        elif render_type == "render_image_massive":

            render_massive_images(audio_folder_path, image_folder_path, combined_audio_folder, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, use_api_DEZGO, api_prompt, api_execution, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores)
        elif render_type == "render_video_massive":

            render_massive_videos(audio_folder_path, video_folder_path, combined_audio_folder, inverted_folder_path, final_video_folder, fade_duration, resolution, fps, video_bitrate, audio_quality, overlay_video, invert_video, encoder, quality_level, aspect_ratio, use_audios_drive, upload_files_drive, upload_files_youtube, randomize_audios, randomize_name, overlay, opacity, blend_mode, preset, pix_fmt, cores)

    else:
        print("Proceso cancelado.")
        return
    
    print("Proceso terminado.")
    return

start_render()
