# Como Instalar e Rodar o Projeto GNSN

Este guia contém os comandos exatos para configurar o ambiente virtual, instalar dependências (ignorando as que exigem compilação C++ como dlib), criar os stubs para o reconhecimento facial, rodar as migrations e subir o servidor.

Abra o terminal (PowerShell) e execute o bloco abaixo **linha por linha** ou cole tudo de uma vez. Certifique-se de estar na pasta raiz do projeto (`C:\Users\Paulo Moraes\GNSN-discentes`):

```powershell
# 1. Garante que você está na pasta raiz do projeto (e não em uma subpasta como /mirim)
cd "C:\Users\Paulo Moraes\GNSN-discentes"

# 2. Cria o ambiente virtual usando o launcher do Python 3.10
# **caso não tenha versão 3.10 instalada**
winget install --id Python.Python.3.10 -e

# se ja estiver instalada
py -3.10 -m venv venv

# 3. Ativa o ambiente virtual
.\venv\Scripts\Activate

# 4. Atualiza o pip
.\venv\Scripts\python.exe -m pip install --upgrade pip

# 5. Remove dependências problemáticas (C++/Desktop) e salva em um novo arquivo
Get-Content requirements.txt | Where-Object { $_ -notmatch 'PySimpleGUI|dlib|face-recognition|faiss|opencv|MiniSom' -and $_.Trim() -ne '' } | Set-Content requirements_filtered.txt

# 6. Instala as dependências base do Django
.\venv\Scripts\python.exe -m pip install -r requirements_filtered.txt

# 7. Instala apenas as bibliotecas de IA que rodam direto (pip install normal)
.\venv\Scripts\python.exe -m pip install opencv-python faiss-cpu face-recognition-models

# 8. Cria os stubs (arquivos falsos) de dlib para evitar erro de importação no Django
New-Item -Path ".\venv\Lib\site-packages\dlib" -ItemType Directory -Force | Out-Null
Set-Content -Path ".\venv\Lib\site-packages\dlib\__init__.py" -Value "# Stub dlib"

# 9. Cria os stubs de face_recognition com as funções mockadas
New-Item -Path ".\venv\Lib\site-packages\face_recognition" -ItemType Directory -Force | Out-Null
$faceRecStub = @"
# Stub face_recognition
def load_image_file(*args, **kwargs): return None
def face_encodings(*args, **kwargs): return []
def face_locations(*args, **kwargs): return []
"@
Set-Content -Path ".\venv\Lib\site-packages\face_recognition\__init__.py" -Value $faceRecStub

# 10. Cria as migrations dos aplicativos locais (app, mirim e patrimonio)
.\venv\Scripts\python.exe manage.py makemigrations app mirim patrimonio

# 11. Aplica as migrations para criar o banco de dados SQLite
.\venv\Scripts\python.exe manage.py migrate

# 12. Cria Super User antes de iniciar
.\venv\Scripts\python.exe manage.py createsuperuser

# 13. Inicia o servidor local
.\venv\Scripts\python.exe manage.py runserver
```

## Após rodar o servidor:
Acesse no seu navegador:
- **Painel:** [http://127.0.0.1:8000/gnsn/camisa/](http://127.0.0.1:8000/gnsn/camisa/)
- **Admin:** [http://127.0.0.1:8000/gnsn/admin/](http://127.0.0.1:8000/gnsn/admin/)
