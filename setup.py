import subprocess
import sys
import os
import ctypes


def install_requirements():
    """
    Installs the required Python packages for SuperPip.
    """
    requirements = [
        "PyQt5",
        "requests",
        "beautifulsoup4"
    ]
    installed_packages = []
    already_installed_packages = []

    for package in requirements:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            installed_packages.append(package)
            print(f"{package} installed successfully.")
        except subprocess.CalledProcessError as e:
            if 'already satisfied' in str(e.output).lower():
                already_installed_packages.append(package)
                print(f"{package} is already installed.")
            else:
                print(f"Failed to install {package}: {e}")
                return False, installed_packages, already_installed_packages

    print("All requirements checked successfully.")
    return True, installed_packages, already_installed_packages


def show_popup(installed_packages, already_installed_packages):
    """
    Show a detailed popup with the installation results.
    """
    message = "Installation Summary:\n\n"
    if installed_packages:
        message += "The following packages were installed successfully:\n"
        message += "\n".join(installed_packages) + "\n\n"
    if already_installed_packages:
        message += "The following packages were already installed:\n"
        message += "\n".join(already_installed_packages) + "\n\n"

    if not installed_packages and not already_installed_packages:
        message += "No packages were installed or already present."

    ctypes.windll.user32.MessageBoxW(0, message, "SuperPip Installer", 1)


def main():
    user_choice = input("Do you want to install the required packages (yes/no)? ").strip().lower()
    if user_choice == 'yes':
        success, installed_packages, already_installed_packages = install_requirements()
        if success:
            show_popup(installed_packages, already_installed_packages)
        else:
            show_popup(installed_packages, already_installed_packages)
    elif user_choice == 'no':
        print("Assuming the requirements are already installed.")
        show_popup([], [])
    else:
        print("Invalid input. Exiting.")
        sys.exit(1)

    # Delete the script file after running
    try:
        os.remove(__file__)
        print("Script deleted successfully.")
    except Exception as e:
        print(f"Failed to delete the script: {e}")


if __name__ == "__main__":
    main()
