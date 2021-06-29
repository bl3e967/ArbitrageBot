import PyInstaller.__main__
import config

PyInstaller.__main__.run([
    "main.py",
    "--name=Arby",
    "--onedir",
    '--distpath=' + config.DIST_PATH, 
    '--workpath=' + config.WORK_PATH
])