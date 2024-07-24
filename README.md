# renderLoop
Loop de videos al toke

Al ejecutar el comando por primera vez te va a crear las carpetas necesarias para poder crear videos con el script

# mac os:

:: Instala Python utilizando Homebrew

brew install python

:: Instala FFmpeg utilizando Homebrew, una herramienta necesaria para el procesamiento de audio y video

brew install ffmpeg

:: Instala la biblioteca, que se utiliza para manipular audio y demas

pip3 install pydub requests google-auth google-auth-oauthlib google-api-python-client

:: Ejecuta el script con

python3 render_module.py


# Windows:
:: Instala Chocolatey

Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

:: Instala Python utilizando Chocolatey

choco install python

:: Instala FFmpeg utilizando Chocolatey, una herramienta necesaria para el procesamiento de audio y video

choco install ffmpeg

:: Instala la biblioteca, que se utiliza para manipular audio y demas

pip install pydub requests google-auth google-auth-oauthlib google-api-python-client

:: Ejecuta el script con

python render_module.py


# SUNO API:

:: Instalar DEPENDENCIAS

cd api-suno

npm install

:: Ejecutar server localmente

npm run dev
