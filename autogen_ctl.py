import os
from git.repo import Repo
from git import Git


ROOT_PATH = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
REPO_PATH = os.path.abspath(os.path.join(ROOT_PATH, ".autogen-repo"))
PATCHES_PATH = os.path.abspath(os.path.join(ROOT_PATH, "autogen-patches"))
GIT_URL = "https://github.com/microsoft/autogen.git"
TARGET_TAG = "v0.2.29"


def ensure_repo():
    # check if repo is valid
    if os.path.exists(REPO_PATH) and os.path.exists(os.path.join(REPO_PATH, ".git")):
        return
    print("Cloning autogen repo")
    Repo.clone_from(GIT_URL, REPO_PATH)


import pip
import importlib.util
def install_editable():
    ensure_repo()
    if importlib.util.find_spec("autogen") is not None:
        return
    print("Installing autogen in editable mode")
    pip.main(["install", "-e", REPO_PATH])


def clean_repo():
    ensure_repo()
    repo = Repo(REPO_PATH)
    git = Git(REPO_PATH)
    # revert local changes
    print("Cleaning repo")
    repo.git.reset("--hard")
    repo.git.clean("-fd")
    # update
    print("Updating repo")
    git.checkout(TARGET_TAG, "-f")


def commit():
    repo = git.Repo(REPO_PATH)
    repo.git.add("--all")
    # check if there's something to stage
    if not repo.index.diff("HEAD"):
        return
    print("Staging changes")
    repo.git.commit("-m", "Current patches staged")


import git
def apply_patches():
    print("Applying patches")
    patches_paths = os.listdir(PATCHES_PATH)
    patches_paths = [os.path.abspath(os.path.join(PATCHES_PATH, p)) for p in patches_paths]
    for patch_path in patches_paths:
        print(f"\tApplying patch {patch_path}")
        repo = git.Repo(REPO_PATH)
        repo.git.apply(["--ignore-space-change", "--ignore-whitespace", patch_path])


def create_patch_from_changes(patch_path: str):
    print("Creating patch from changes")
    repo = git.Repo(REPO_PATH)
    patch_content = repo.git.diff("--patch")
    with open(patch_path, "wt", encoding="utf-8") as f:
        f.write(patch_content)
        f.write("\n")


def next_patch_path():
    num = 0
    while True:
        prefix = f"{num:03}"
        found = False
        for patch in os.listdir(PATCHES_PATH):
            if patch.startswith(prefix):
                found = True
                break
        if not found:
            return os.path.abspath(os.path.join(PATCHES_PATH, f"{prefix}-new-patch.diff"))
        num += 1


def setup():
    print("Setting up repo for use")
    ensure_repo()
    clean_repo()
    apply_patches()
    install_editable()


def create_patch():
    print("Creating new patch")
    ensure_repo()
    clean_repo()
    apply_patches()
    commit()
    
    input("Do your changes and press enter to create patch")
    path = next_patch_path()
    create_patch_from_changes(path)

    clean_repo()
    apply_patches()


if __name__ == "__main__":
    choice = input("Setup or create patch? (s/c): ")
    if choice == "s":
        setup()
    elif choice == "c":
        create_patch()
    else:
        print("Invalid choice")
        exit(1)
