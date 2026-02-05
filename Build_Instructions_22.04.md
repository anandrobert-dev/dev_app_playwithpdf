# 🚀 Deployment Guide: Building on Ubuntu 22.04

To ensure your app works on all 50 machines, you must build it on your **Ubuntu 22.04** machine.

## 📦 Step 1: Copy Files to Flash Drive

Create a new folder on your flash drive (e.g., `Oi360_Source`) and copy **ONLY** these files and folders into it.

### ✅ Folders to Copy

* `assets/`
* `gui/`
* `pdf_utils/`

### ✅ Files to Copy

* `main.py`
* `requirements.txt`
* `oi360_logo.png` (The image file in the root folder)
* `install.sh` (We will need this later)
* `uninstall.sh`

### ❌ DO NOT Copy (Skip these)

* `venv/`
* `build/`
* `dist/`
* `.git/`
* `__pycache__/` folders

---

## 🛠️ Step 2: Set Up on Ubuntu 22.04

1. **Paste the Folder**: Copy the `Oi360_Source` folder from your flash drive to the destination computer (e.g., to the Desktop).
2. **Open Terminal**: Right-click inside that folder and select **"Open in Terminal"**.

### 1. Install System Requirements

Run this command to get the necessary tools:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev build-essential libgl1-mesa-dev libxkbcommon-x11-0
```

### 2. Setup Python Environment

Run these commands one by one:

```bash
# Create a fresh virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
```

---

## 🏗️ Step 3: Build the App

Run this exact command to create the executable:

```bash
pyinstaller --noconfirm --onefile --windowed --name "Oi360_Suite" \
 --add-data "gui:gui" \
 --add-data "pdf_utils:pdf_utils" \
 --add-data "oi360_logo.png:." \
 --hidden-import "PyQt5" \
 --hidden-import "pypdf" \
 main.py
```

---

## 🚀 Step 4: Verify & Deploy

1. **Check the Output**: You will now see a new `dist` folder.
2. **Test It**: Run `./dist/Oi360_Suite` to make sure it opens.
3. **Prepare for Fleet**:
    The file `dist/Oi360_Suite` is your "Gold Master". This is the **only file** you need to copy to the other 50 machines (along with `install.sh` and `logo.png` if you want the desktop shortcuts).
