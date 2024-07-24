# renderLoop
Loop de videos al toke

Al ejecutar el comando por primera vez te va a crear las carpetas necesarias para poder crear videos con el script

# mac os:

:: Instala Python utilizando Homebrew

```bash
brew install python
```

:: Instala FFmpeg utilizando Homebrew, una herramienta necesaria para el procesamiento de audio y video

```bash
brew install ffmpeg
```

:: Instala la biblioteca, que se utiliza para manipular audio y demas

```bash
pip3 install -r requirements.txt
```

:: Ejecuta el script con

```bash
python3 render_module.py
```

# Windows:
:: Instala Chocolatey

```bash
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

:: Instala Python utilizando Chocolatey

```bash
choco install python
```

:: Instala FFmpeg utilizando Chocolatey, una herramienta necesaria para el procesamiento de audio y video

```bash
choco install ffmpeg
```

:: Instala la biblioteca, que se utiliza para manipular audio y demas

```bash
pip install -r requirements.txt
```

:: Ejecuta el script con

```bash
python render_module.py
```

# SUNO API:

:: Instalar DEPENDENCIAS

```bash
cd api-suno
npm install
```

:: Ejecutar server localmente

```bash
npm run dev
```