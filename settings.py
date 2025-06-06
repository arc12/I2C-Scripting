PORT = "COM4"
# faster rates do not give faster loops in Python. Can get 5.5ms per loop iteration for a 3-axis read. Can get down a fraction with 1 axis.
# opening/closine each 3-axis read increases to ~10ms
BAUD = 115200
READ_TIMEOUT = 0.5  # s

# no need for CR or LF