# IdentityV Login Helper
Login utility that enables password login in IdentityV PC client. \
Forked from [idv-login](https://github.com/Alexander-Porter/idv-login) and [idv-login-for-mac](https://github.com/lszghcpp/idv-login-for-mac).

## Usage
1. Clone the git repository. \
    `git clone https://github.com/FeyXieXzf/identityv-login-helper.git` \
    `cd ./identityv-login-helper`
2. Install required Python modules. \
    PyPi: `pip install -r requirements.txt` \
    Arch: `sudo pacman -Syu python-cryptography python-faker python-flask python-gevent python-psutil python-pycryptodome python-pyperclip python-requests python-requests-toolbelt`
3. Run the script with sudo. \
    `sudo python main.py`