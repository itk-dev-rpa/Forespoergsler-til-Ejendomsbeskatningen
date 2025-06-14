"""This module contains configuration constants used across the framework"""

# The number of times the robot retries on an error before terminating.
MAX_RETRY_COUNT = 5

# Whether the robot should be marked as failed if MAX_RETRY_COUNT is reached.
FAIL_ROBOT_ON_TOO_MANY_ERRORS = False

# Error screenshot config
SMTP_SERVER = "smtp.adm.aarhuskommune.dk"
SMTP_PORT = 25
SCREENSHOT_SENDER = "robot@friend.dk"

# Constant/Credential names
ERROR_EMAIL = "Error Email"
GRAPH_API = "Graph API"
STRUCTURA_LOGIN = "KMD Ejendomsbeskatning"
SAP_LOGIN = "SAP Ejendomsbeskatning"

# GetOrganized
GO_API = "https://ad.go.aarhuskommune.dk"
GO_CREDENTIALS = "GetOrganized Login"
GO_TIMEOUT = 60
