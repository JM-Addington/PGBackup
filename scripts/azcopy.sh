# Download 64-bit version of AzCopy if on x86_64 architecture
# https://aka.ms/downloadazcopy-v10-linux

if [ "$(uname -m)" = "x86_64" ]; then
    wget -O azcopy.tar.gz https://aka.ms/downloadazcopy-v10-linux
fi

# ARM64 architecture
if [ "$(uname -m)" = "aarch64" ]; then
    wget -O azcopy.tar.gz https://aka.ms/downloadazcopy-v10-linux-arm64
fi

tar -xf azcopy.tar.gz --strip-components=1 --wildcards '*/azcopy'

# First argument is the backup file, the second is supposed to be the URL + SAS token
# set as an environment variable.
./azcopy copy $1 $AZCOPY