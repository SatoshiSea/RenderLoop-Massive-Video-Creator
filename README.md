# renderLoop
Loop de videos al toke

mac os:

:: Instala Python utilizando Homebrew
brew install python

:: Instala FFmpeg utilizando Homebrew, una herramienta necesaria para el procesamiento de audio y video
brew install ffmpeg

:: Instala la biblioteca, que se utiliza para manipular audio y demas
pip3 install pydub
pip3 install requests
pip3 install tkinter
pip3 install google-auth
pip3 install google-auth-oauthlib
pip3 install google-api-python-client

:: Ejecuta el script on
python3 render_module.py


Windows:
:: Instala Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

:: Instala Python utilizando Chocolatey
choco install python

:: Instala FFmpeg utilizando Chocolatey, una herramienta necesaria para el procesamiento de audio y video
choco install ffmpeg

:: Instala la biblioteca, que se utiliza para manipular audio y demas
pip install pydub
pip install requests
pip install tkinter
pip install google-auth
pip install google-auth-oauthlib
pip install google-api-python-client


:: Ejecuta el script
python render_module.py
