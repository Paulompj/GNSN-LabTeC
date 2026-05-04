# Projeto GNSN — Guia de Instalação e Execução

Este documento descreve o passo a passo para configurar o ambiente de desenvolvimento e executar o projeto **GNSN** localmente.

## Tecnologias Utilizadas

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![FAISS](https://img.shields.io/badge/FAISS-0467DF?logo=meta&logoColor=white)](https://github.com/facebookresearch/faiss)
[![Face Recognition](https://img.shields.io/badge/Face%20Recognition-Models-orange)](https://github.com/ageitgey/face_recognition)
[![Pip](https://img.shields.io/badge/Pip-3776AB?logo=python&logoColor=white)](https://pip.pypa.io/)
[![Virtualenv](https://img.shields.io/badge/Virtualenv-4B8BBE?logo=python&logoColor=white)](https://docs.python.org/3/library/venv.html)
[![PowerShell](https://img.shields.io/badge/PowerShell-5391FE?logo=powershell&logoColor=white)](https://learn.microsoft.com/powershell/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
---

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- Python 3.10+
- Git
- Windows PowerShell
- Winget (gerenciador de pacotes do Windows)

---

## Estrutura esperada

Certifique-se de estar na pasta raiz do projeto:
- C:\Users\Seu Usuário\GNSN-discentes


---

## Passo a passo de instalação

Execute os comandos abaixo no **PowerShell**:

>  Você pode rodar linha por linha ou colar tudo de uma vez.

```powershell
# 1. Acessa a pasta do projeto
cd "C:\Users\Seu Usuário\GNSN-discentes"

# 2. Instala Python 3.10 (caso não tenha)
winget install --id Python.Python.3.10 -e

# 3. Cria o ambiente virtual
py -3.10 -m venv venv

# 4. Ativa o ambiente virtual
.\venv\Scripts\Activate

# 5. Atualiza o pip
.\venv\Scripts\python.exe -m pip install --upgrade pip

# 6. Remove dependências problemáticas (C++)
Get-Content requirements.txt | Where-Object { $_ -notmatch 'PySimpleGUI|dlib|face-recognition|faiss|opencv|MiniSom' -and $_.Trim() -ne '' } | Set-Content requirements_filtered.txt

# 7. Instala dependências principais
.\venv\Scripts\python.exe -m pip install -r requirements_filtered.txt

# 8. Instala bibliotecas compatíveis com pip
.\venv\Scripts\python.exe -m pip install opencv-python faiss-cpu face-recognition-models
```

## Configuração de Stubs (Workaround)

Algumas bibliotecas como dlib exigem compilação em C++, o que pode causar erros. Para evitar isso, criamos stubs (implementações falsas).

```powershell
# Stub para dlib
New-Item -Path ".\venv\Lib\site-packages\dlib" -ItemType Directory -Force | Out-Null
Set-Content -Path ".\venv\Lib\site-packages\dlib\__init__.py" -Value "# Stub dlib"

# Stub para face_recognition
New-Item -Path ".\venv\Lib\site-packages\face_recognition" -ItemType Directory -Force | Out-Null

$faceRecStub = @"
# Stub face_recognition
def load_image_file(*args, **kwargs): return None
def face_encodings(*args, **kwargs): return []
def face_locations(*args, **kwargs): return []
"@

Set-Content -Path ".\venv\Lib\site-packages\face_recognition\__init__.py" -Value $faceRecStub
```

## Banco de dados

```powershell
# Cria migrations
.\venv\Scripts\python.exe manage.py makemigrations app mirim patrimonio

# Aplica migrations (SQLite)
.\venv\Scripts\python.exe manage.py migrate
```
## Criar o usuário administrador
```powershell
.\venv\Scripts\python.exe manage.py createsuperuser
```
## Executar o projeto

```powershell
.\venv\Scripts\python.exe manage.py runserver
```

## Acesse no navegador

```powershell
http://127.0.0.1:8000/gnsn/camisa/login/
```

## Observações importantes

- As bibliotecas dlib e face_recognition foram simuladas (stubs)
- Funcionalidades de reconhecimento facial podem não funcionar completamente
