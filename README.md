# yinegelos-cleaner
YinegelOS Cleaner is Python Customtkinter based application. YinegelOS Cleaner helps you to clean your Debian based Operating System.
## Compile
If you are compiling this application on a Debian 12 or higher system, you should know the following: customtkinter, a dependency of this application, is included in PEP 668 with Debian 12, install this dependency by creating a virtual environment (venv) in Python,

and using the command: pip install customtkinter

Please compile this application with pyinstaller. You can download and install the "pyinstaller" library in your virtual environment with the following command:

pip install pyinstaller

The pyinstaller command required to compile this application is:

pyinstaller --onefile --windowed YinegelOS_Cleaner.py

Please be in your Python virtual environment and in the same directory as the YinegelOS_Cleaner.py file when running this command.

After the command is complete, the executable file will be found in the dist folder. You can delete the build folder. The execution permissions (chmod +x) for the executable file in the dist folder have been granted by pyinstaller.
