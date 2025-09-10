The venv also has pycrc, which can be used to generate c code to implement CRC calculations.

https://pycrc.org/index.html

Use the CRC folder for output.


## For SFM3003
- Width         = 8
- Poly          = 0x31
- XorIn         = 0xff
- ReflectIn     = False
- XorOut        = 0x00
- ReflectOut    = False

Check model specification using:  
pycrc --verbose --check-hexstring BEEF --width 8 --poly 0x31 --reflect-in false --xor-in 0xFF --reflect-out false --xor-out 0x00

Generate code using:
pycrc --verbose --width 8 --poly 0x31 --reflect-in false --xor-in 0xFF --reflect-out false --xor-out 0x00 --algorithm table-driven --table-idx-width 4 --generate h -o crc_sfm3003.h
and
pycrc --verbose --width 8 --poly 0x31 --reflect-in false --xor-in 0xFF --reflect-out false --xor-out 0x00 --algorithm table-driven --table-idx-width 4 --generate c -o crc_sfm3003.c