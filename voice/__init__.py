# Mac not-imports
import platform
if not platform.mac_ver()[0]:
	from recognition import VoiceRecognition
from commands import interpret_command
